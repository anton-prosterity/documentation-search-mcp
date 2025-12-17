#!/usr/bin/env python3
"""
Serper-free documentation site search.

This module provides a Serper-free fallback for `site:` queries by:

1) Preferring docs-native search indexes when available (MkDocs / Sphinx)
2) Falling back to sitemap discovery (robots.txt + sitemap.xml)
3) Optionally using a Playwright-backed fetcher to score/snippet page content
"""

from __future__ import annotations

import asyncio
import gzip
import json
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


_SITEMAP_CACHE_TTL = timedelta(hours=24)
_INDEX_CACHE_TTL = timedelta(hours=24)
_MAX_SITEMAP_URLS = 50_000
_MAX_SITEMAPS_TO_FETCH = 12
_MAX_INDEX_BYTES = 10_000_000
_MAX_INDEX_DOC_TEXT_CHARS = 5_000
_DEFAULT_CONTENT_FETCH_CONCURRENCY = 3


@dataclass(frozen=True)
class _SitemapCacheEntry:
    fetched_at: datetime
    urls: Tuple[str, ...]


_sitemap_cache: Dict[str, _SitemapCacheEntry] = {}
_sitemap_locks: Dict[str, asyncio.Lock] = {}


@dataclass(frozen=True)
class _IndexCacheEntry:
    fetched_at: datetime
    kind: str
    payload: Any


_index_cache: Dict[str, _IndexCacheEntry] = {}
_index_locks: Dict[str, asyncio.Lock] = {}


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        try:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            parsed = parsed.replace(tzinfo=None)
    return parsed


def export_preindexed_state() -> Dict[str, Any]:
    """Export in-memory sitemap/index caches for persistence."""
    now = datetime.now()
    sitemaps: Dict[str, Dict[str, Any]] = {}
    for origin, entry in _sitemap_cache.items():
        sitemaps[origin] = {
            "fetched_at": entry.fetched_at.isoformat(),
            "urls": list(entry.urls),
        }

    indexes: Dict[str, Dict[str, Any]] = {}
    for index_url, entry in _index_cache.items():
        payload = entry.payload
        if isinstance(payload, tuple):
            payload = list(payload)

        indexes[index_url] = {
            "fetched_at": entry.fetched_at.isoformat(),
            "kind": entry.kind,
            "payload": payload,
        }

    return {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "sitemaps": sitemaps,
        "indexes": indexes,
    }


def import_preindexed_state(state: Any) -> None:
    """Import previously persisted sitemap/index caches."""
    if not isinstance(state, dict):
        return

    imported_at = datetime.now()
    max_future_skew = timedelta(days=1)

    sitemaps = state.get("sitemaps")
    if isinstance(sitemaps, dict):
        for origin, entry in sitemaps.items():
            if not isinstance(origin, str) or not isinstance(entry, dict):
                continue
            urls_raw = entry.get("urls")
            if not isinstance(urls_raw, list):
                continue
            urls = tuple(str(url).strip() for url in urls_raw if str(url).strip())
            if not urls:
                continue
            fetched_at = _parse_iso_datetime(entry.get("fetched_at"))
            if fetched_at is None or fetched_at > imported_at + max_future_skew:
                fetched_at = imported_at
            _sitemap_cache[origin] = _SitemapCacheEntry(
                fetched_at=fetched_at, urls=urls
            )

    indexes = state.get("indexes")
    if isinstance(indexes, dict):
        for index_url, entry in indexes.items():
            if not isinstance(index_url, str) or not isinstance(entry, dict):
                continue
            kind = entry.get("kind")
            payload_raw = entry.get("payload")
            if not isinstance(kind, str):
                continue

            if kind == "mkdocs":
                if not isinstance(payload_raw, list):
                    continue
                prepared = []
                for doc in payload_raw:
                    if not isinstance(doc, dict):
                        continue
                    location = str(doc.get("location") or "").strip()
                    if not location:
                        continue
                    title = str(doc.get("title") or "").strip()
                    text = str(doc.get("text") or "").strip()
                    if len(text) > _MAX_INDEX_DOC_TEXT_CHARS:
                        text = text[:_MAX_INDEX_DOC_TEXT_CHARS]
                    prepared.append(
                        {"location": location, "title": title, "text": text}
                    )
                if not prepared:
                    continue
                payload: Any = tuple(prepared)
            elif kind == "sphinx":
                if not isinstance(payload_raw, dict):
                    continue
                payload = payload_raw
            else:
                continue

            fetched_at = _parse_iso_datetime(entry.get("fetched_at"))
            if fetched_at is None or fetched_at > imported_at + max_future_skew:
                fetched_at = imported_at

            _index_cache[index_url] = _IndexCacheEntry(
                fetched_at=fetched_at, kind=kind, payload=payload
            )


def load_preindexed_state(path: str) -> bool:
    """Load a persisted index cache from disk into memory."""
    if not path:
        return False
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return False
    import_preindexed_state(raw)
    return True


def save_preindexed_state(path: str) -> None:
    """Persist current in-memory sitemap/index caches to disk."""
    if not path:
        raise ValueError("persist path must be non-empty")
    state = export_preindexed_state()
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    os.replace(tmp_path, path)


def _get_cached_index_from_memory(index_url: str, *, kind: str) -> Optional[Any]:
    cache_entry = _index_cache.get(index_url)
    if cache_entry and cache_entry.kind == kind:
        return cache_entry.payload
    return None


def _get_cached_sitemap_urls_from_memory(
    origin: str, *, allow_stale: bool
) -> Optional[List[str]]:
    cache_entry = _sitemap_cache.get(origin)
    if not cache_entry:
        return None
    if not cache_entry.urls:
        return None
    if allow_stale:
        return list(cache_entry.urls)
    if datetime.now() - cache_entry.fetched_at <= _SITEMAP_CACHE_TTL:
        return list(cache_entry.urls)
    return None


async def preindex_site(
    site_url: str,
    client: httpx.AsyncClient,
    *,
    user_agent: str,
    include_sitemap: bool = False,
) -> Dict[str, Any]:
    """Fetch and cache on-site search indexes for a docs site."""
    parsed = urlparse(site_url)
    if not parsed.scheme or not parsed.netloc:
        return {"site_url": site_url, "status": "invalid_url"}

    origin = f"{parsed.scheme}://{parsed.netloc}"
    results: Dict[str, Any] = {
        "site_url": site_url,
        "origin": origin,
        "mkdocs_index": None,
        "sphinx_index": None,
        "sitemap": None,
        "errors": [],
    }

    for index_url in _mkdocs_index_candidates(site_url):
        try:
            docs = await _get_cached_index(
                client,
                index_url,
                user_agent=user_agent,
                kind="mkdocs",
                timeout_seconds=20.0,
            )
        except Exception as e:
            results["errors"].append(f"mkdocs:{index_url}: {e}")
            continue
        if docs:
            results["mkdocs_index"] = {"index_url": index_url, "documents": len(docs)}
            break

    for index_url in _sphinx_index_candidates(site_url):
        try:
            index = await _get_cached_index(
                client,
                index_url,
                user_agent=user_agent,
                kind="sphinx",
                timeout_seconds=20.0,
            )
        except Exception as e:
            results["errors"].append(f"sphinx:{index_url}: {e}")
            continue
        if isinstance(index, dict):
            filenames = index.get("filenames")
            results["sphinx_index"] = {
                "index_url": index_url,
                "documents": len(filenames) if isinstance(filenames, list) else None,
            }
            break

    if include_sitemap:
        try:
            urls = await _load_site_sitemap_urls(
                client, site_url, user_agent=user_agent
            )
            if urls:
                _sitemap_cache[origin] = _SitemapCacheEntry(
                    fetched_at=datetime.now(), urls=tuple(urls)
                )
                results["sitemap"] = {"urls": len(urls)}
        except Exception as e:
            results["errors"].append(f"sitemap:{origin}: {e}")

    results["status"] = (
        "ok"
        if results.get("mkdocs_index")
        or results.get("sphinx_index")
        or results.get("sitemap")
        else "no_index_found"
    )
    return results


def _parse_site_query(query: str) -> Tuple[Optional[str], str]:
    match = re.search(r"\bsite:(\S+)", query)
    if not match:
        return None, query.strip()

    site_token = match.group(1).strip().strip('"').strip("'")
    remaining = (query[: match.start()] + query[match.end() :]).strip()
    return site_token, remaining


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "these",
    "this",
    "to",
    "using",
    "what",
    "when",
    "where",
    "why",
    "with",
}


def _tokenize_query(text: str) -> List[str]:
    tokens = [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t]
    filtered: List[str] = []
    for token in tokens:
        if token in _STOPWORDS:
            continue
        if len(token) <= 1:
            continue
        if token not in filtered:
            filtered.append(token)
    return filtered[:12]


def _matches_site_prefix(candidate_url: str, site_url: str) -> bool:
    try:
        candidate = urlparse(candidate_url)
        site = urlparse(site_url)
    except Exception:
        return False

    if not candidate.netloc or candidate.netloc.lower() != site.netloc.lower():
        return False

    site_path = site.path or "/"
    candidate_path = candidate.path or "/"

    site_path_norm = site_path.rstrip("/")
    candidate_path_norm = candidate_path.rstrip("/")

    if site_path_norm in ("", "/"):
        return True

    return candidate_path_norm == site_path_norm or candidate_path_norm.startswith(
        f"{site_path_norm}/"
    )


def _sitemap_candidates(site_url: str) -> List[str]:
    parsed = urlparse(site_url)
    if not parsed.scheme or not parsed.netloc:
        return []

    origin = f"{parsed.scheme}://{parsed.netloc}"
    site_base = site_url.rstrip("/")

    candidates = [
        f"{origin}/sitemap.xml",
        f"{origin}/sitemap_index.xml",
        f"{origin}/sitemap-index.xml",
    ]

    if site_base != origin:
        candidates.extend(
            [
                f"{site_base}/sitemap.xml",
                f"{site_base}/sitemap_index.xml",
            ]
        )

    # Deduplicate while preserving order.
    seen = set()
    unique: List[str] = []
    for item in candidates:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def _mkdocs_index_candidates(site_url: str) -> List[str]:
    parsed = urlparse(site_url)
    if not parsed.scheme or not parsed.netloc:
        return []

    origin = f"{parsed.scheme}://{parsed.netloc}/"
    base = site_url.rstrip("/") + "/"

    candidates = [
        urljoin(base, "search/search_index.json"),
        urljoin(base, "search_index.json"),
    ]
    if base != origin:
        candidates.extend(
            [
                urljoin(origin, "search/search_index.json"),
                urljoin(origin, "search_index.json"),
            ]
        )

    seen: set[str] = set()
    unique: List[str] = []
    for item in candidates:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def _mkdocs_base_from_index_url(index_url: str) -> str:
    suffixes = ("/search/search_index.json", "/search_index.json")
    for suffix in suffixes:
        if index_url.endswith(suffix):
            return index_url[: -len(suffix)] + "/"
    return urljoin(index_url, "./")


def _sphinx_index_candidates(site_url: str) -> List[str]:
    parsed = urlparse(site_url)
    if not parsed.scheme or not parsed.netloc:
        return []

    origin = f"{parsed.scheme}://{parsed.netloc}/"
    base = site_url.rstrip("/") + "/"

    candidates = [urljoin(base, "searchindex.js")]
    if base != origin:
        candidates.append(urljoin(origin, "searchindex.js"))

    seen: set[str] = set()
    unique: List[str] = []
    for item in candidates:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def _sphinx_base_from_index_url(index_url: str) -> str:
    if index_url.endswith("/searchindex.js"):
        return index_url[: -len("/searchindex.js")] + "/"
    if index_url.endswith("searchindex.js"):
        return index_url[: -len("searchindex.js")]
    return urljoin(index_url, "./")


async def _fetch_bytes(
    client: httpx.AsyncClient, url: str, *, user_agent: str, timeout_seconds: float
) -> Optional[bytes]:
    try:
        response = await client.get(
            url,
            headers={"User-Agent": user_agent},
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
        )
        if response.status_code >= 400:
            return None
        return response.content
    except Exception:
        return None


def _maybe_decompress_gzip(blob: bytes) -> bytes:
    # Some sitemaps are served as *.gz without Content-Encoding headers.
    if len(blob) >= 2 and blob[0] == 0x1F and blob[1] == 0x8B:
        try:
            return gzip.decompress(blob)
        except Exception:
            return blob
    return blob


def _xml_root_tag(root: ET.Element) -> str:
    if "}" in root.tag:
        return root.tag.split("}", 1)[1]
    return root.tag


def _parse_sitemap_xml(blob: bytes) -> Tuple[List[str], List[str]]:
    """
    Returns (urls, child_sitemaps).
    """
    try:
        root = ET.fromstring(blob)
    except Exception:
        return [], []

    tag = _xml_root_tag(root)
    if tag == "urlset":
        urls = [
            (loc.text or "").strip()
            for loc in root.findall(".//{*}url/{*}loc")
            if (loc.text or "").strip()
        ]
        return urls, []

    if tag == "sitemapindex":
        sitemaps = [
            (loc.text or "").strip()
            for loc in root.findall(".//{*}sitemap/{*}loc")
            if (loc.text or "").strip()
        ]
        return [], sitemaps

    return [], []


async def _discover_sitemaps_from_robots(
    client: httpx.AsyncClient, site_url: str, *, user_agent: str
) -> List[str]:
    parsed = urlparse(site_url)
    if not parsed.scheme or not parsed.netloc:
        return []
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = await client.get(
            robots_url,
            headers={"User-Agent": user_agent},
            timeout=httpx.Timeout(10.0),
            follow_redirects=True,
        )
        if response.status_code >= 400:
            return []
        sitemaps = []
        for line in response.text.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap = line.split(":", 1)[1].strip()
                if sitemap:
                    sitemaps.append(sitemap)
        return sitemaps
    except Exception:
        return []


async def _load_site_sitemap_urls(
    client: httpx.AsyncClient,
    site_url: str,
    *,
    user_agent: str,
    allow_html_fallback: bool = True,
) -> List[str]:
    sitemap_urls = await _discover_sitemaps_from_robots(
        client, site_url, user_agent=user_agent
    )
    sitemap_urls.extend(_sitemap_candidates(site_url))

    visited_sitemaps = set()
    sitemap_queue = []
    for sitemap_url in sitemap_urls:
        if sitemap_url and sitemap_url not in visited_sitemaps:
            sitemap_queue.append(sitemap_url)
            visited_sitemaps.add(sitemap_url)

    discovered_urls: List[str] = []
    seen_urls = set()

    while sitemap_queue and len(visited_sitemaps) <= _MAX_SITEMAPS_TO_FETCH:
        sitemap_url = sitemap_queue.pop(0)

        blob = await _fetch_bytes(
            client, sitemap_url, user_agent=user_agent, timeout_seconds=15.0
        )
        if not blob:
            continue

        blob = _maybe_decompress_gzip(blob)
        urls, child_sitemaps = _parse_sitemap_xml(blob)

        for url in urls:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            discovered_urls.append(url)
            if len(discovered_urls) >= _MAX_SITEMAP_URLS:
                return discovered_urls

        for child in child_sitemaps:
            if child in visited_sitemaps:
                continue
            if len(visited_sitemaps) >= _MAX_SITEMAPS_TO_FETCH:
                break
            visited_sitemaps.add(child)
            sitemap_queue.append(child)

    if discovered_urls:
        return discovered_urls

    if not allow_html_fallback:
        return []

    return await _discover_urls_from_html_links(client, site_url, user_agent=user_agent)


async def _discover_urls_from_html_links(
    client: httpx.AsyncClient, site_url: str, *, user_agent: str
) -> List[str]:
    """Discover internal links from the site's HTML when no sitemap is available."""
    parsed = urlparse(site_url)
    if not parsed.scheme or not parsed.netloc:
        return []
    origin = f"{parsed.scheme}://{parsed.netloc}"
    base_for_join = site_url.rstrip("/") + "/"

    html_blob = await _fetch_bytes(
        client, site_url, user_agent=user_agent, timeout_seconds=15.0
    )
    if not html_blob:
        return []

    try:
        html_text = html_blob.decode("utf-8", errors="ignore")
    except Exception:
        return []

    soup = BeautifulSoup(html_text, "html.parser")
    discovered_from_html: List[str] = []
    seen_html_urls: set[str] = set()

    def _is_asset_path(path: str) -> bool:
        return bool(
            re.search(
                r"\.(?:png|jpe?g|gif|svg|webp|css|js|map|ico|woff2?|ttf|otf|eot|pdf|zip|gz)$",
                path.lower(),
            )
        )

    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "").strip()
        if not href:
            continue
        lower = href.lower()
        if lower.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue

        absolute = urljoin(base_for_join, href)
        parsed_link = urlparse(absolute)
        if parsed_link.scheme not in {"http", "https"}:
            continue
        if parsed_link.netloc.lower() != parsed.netloc.lower():
            continue
        if _is_asset_path(parsed_link.path or ""):
            continue

        sanitized = parsed_link._replace(query="", fragment="").geturl()
        if not sanitized.startswith(origin):
            continue
        if sanitized in seen_html_urls:
            continue
        seen_html_urls.add(sanitized)
        discovered_from_html.append(sanitized)
        if len(discovered_from_html) >= _MAX_SITEMAP_URLS:
            break

    return discovered_from_html


def _extract_text_snippet(text: str, tokens: Sequence[str]) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return ""

    if not tokens:
        return cleaned[:240]

    lower = cleaned.lower()
    best_idx: Optional[int] = None
    for token in tokens:
        idx = lower.find(token)
        if idx == -1:
            continue
        if best_idx is None or idx < best_idx:
            best_idx = idx

    if best_idx is None:
        return cleaned[:240]

    start = max(0, best_idx - 80)
    end = min(len(cleaned), best_idx + 160)
    return cleaned[start:end].strip()[:240]


def _score_urls(urls: Iterable[str], tokens: Sequence[str]) -> List[Tuple[int, str]]:
    scored: List[Tuple[int, str]] = []
    if not tokens:
        return [(1, url) for url in urls]

    for url in urls:
        url_lower = url.lower()
        score = 0
        for token in tokens:
            if token not in url_lower:
                continue
            score += 1
            # Boost for segment-level matches.
            path = urlparse(url).path.lower()
            segments = [seg for seg in re.split(r"[/._-]+", path) if seg]
            if token in segments:
                score += 6
            else:
                score += 2
        if score > 0:
            scored.append((score, url))
    scored.sort(key=lambda item: (-item[0], len(item[1])))
    return scored


def _fallback_title_from_url(url: str) -> str:
    parsed = urlparse(url)
    segment = (parsed.path or "/").rstrip("/").split("/")[-1]
    segment = re.sub(r"\.[a-z0-9]+$", "", segment, flags=re.IGNORECASE)
    segment = segment.replace("-", " ").replace("_", " ").strip()
    if not segment:
        return url
    return segment[:1].upper() + segment[1:]


def _extract_page_snippet(soup: BeautifulSoup, tokens: Sequence[str]) -> str:
    for meta_name in ("description", "og:description"):
        meta = soup.find("meta", attrs={"name": meta_name}) or soup.find(
            "meta", attrs={"property": meta_name}
        )
        if meta and meta.get("content"):
            return str(meta["content"]).strip()[:240]

    text = soup.get_text(" ", strip=True)
    if not text:
        return ""

    if not tokens:
        return text[:240]

    text_lower = text.lower()
    for token in tokens:
        idx = text_lower.find(token)
        if idx == -1:
            continue
        start = max(0, idx - 80)
        end = min(len(text), idx + 160)
        snippet = text[start:end].strip()
        return snippet[:240]

    return text[:240]


async def _fetch_result_metadata(
    client: httpx.AsyncClient, url: str, *, user_agent: str, tokens: Sequence[str]
) -> Dict[str, str]:
    try:
        response = await client.get(
            url,
            headers={"User-Agent": user_agent},
            timeout=httpx.Timeout(12.0),
            follow_redirects=True,
        )
        if response.status_code >= 400:
            return {"title": _fallback_title_from_url(url), "snippet": ""}
        soup = BeautifulSoup(response.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""
        if not title:
            title = _fallback_title_from_url(url)
        snippet = _extract_page_snippet(soup, tokens)
        return {"title": title, "snippet": snippet}
    except Exception:
        return {"title": _fallback_title_from_url(url), "snippet": ""}


async def _get_cached_index(
    client: httpx.AsyncClient,
    index_url: str,
    *,
    user_agent: str,
    kind: str,
    timeout_seconds: float,
) -> Optional[Any]:
    now = datetime.now()
    cache_entry = _index_cache.get(index_url)
    stale_payload: Optional[Any] = None
    if cache_entry and cache_entry.kind == kind:
        stale_payload = cache_entry.payload
    if (
        cache_entry
        and cache_entry.kind == kind
        and now - cache_entry.fetched_at <= _INDEX_CACHE_TTL
    ):
        return cache_entry.payload

    lock = _index_locks.setdefault(index_url, asyncio.Lock())
    async with lock:
        cache_entry = _index_cache.get(index_url)
        if (
            cache_entry
            and cache_entry.kind == kind
            and now - cache_entry.fetched_at <= _INDEX_CACHE_TTL
        ):
            return cache_entry.payload
        if cache_entry and cache_entry.kind == kind:
            stale_payload = cache_entry.payload

        blob = await _fetch_bytes(
            client, index_url, user_agent=user_agent, timeout_seconds=timeout_seconds
        )
        if (not blob or len(blob) > _MAX_INDEX_BYTES) and stale_payload is not None:
            _index_cache[index_url] = _IndexCacheEntry(
                fetched_at=datetime.now(), kind=kind, payload=stale_payload
            )
            return stale_payload
        if not blob or len(blob) > _MAX_INDEX_BYTES:
            return None

        payload: Any
        if kind == "mkdocs":
            try:
                raw = json.loads(blob.decode("utf-8"))
            except Exception:
                if stale_payload is not None:
                    _index_cache[index_url] = _IndexCacheEntry(
                        fetched_at=datetime.now(), kind=kind, payload=stale_payload
                    )
                return stale_payload
            docs = raw.get("docs")
            if not isinstance(docs, list):
                if stale_payload is not None:
                    _index_cache[index_url] = _IndexCacheEntry(
                        fetched_at=datetime.now(), kind=kind, payload=stale_payload
                    )
                return stale_payload

            prepared = []
            for doc in docs:
                if not isinstance(doc, dict):
                    continue
                location = str(doc.get("location") or "").strip()
                title = str(doc.get("title") or "").strip()
                text = str(doc.get("text") or "").strip()
                if len(text) > _MAX_INDEX_DOC_TEXT_CHARS:
                    text = text[:_MAX_INDEX_DOC_TEXT_CHARS]
                if not location:
                    continue
                prepared.append({"location": location, "title": title, "text": text})

            payload = tuple(prepared)
        elif kind == "sphinx":
            try:
                text = blob.decode("utf-8", errors="ignore")
            except Exception:
                if stale_payload is not None:
                    _index_cache[index_url] = _IndexCacheEntry(
                        fetched_at=datetime.now(), kind=kind, payload=stale_payload
                    )
                return stale_payload

            marker = "Search.setIndex("
            idx = text.find(marker)
            if idx == -1:
                if stale_payload is not None:
                    _index_cache[index_url] = _IndexCacheEntry(
                        fetched_at=datetime.now(), kind=kind, payload=stale_payload
                    )
                return stale_payload
            start = text.find("{", idx)
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                if stale_payload is not None:
                    _index_cache[index_url] = _IndexCacheEntry(
                        fetched_at=datetime.now(), kind=kind, payload=stale_payload
                    )
                return stale_payload
            json_text = text[start : end + 1]
            try:
                payload = json.loads(json_text)
            except Exception:
                if stale_payload is not None:
                    _index_cache[index_url] = _IndexCacheEntry(
                        fetched_at=datetime.now(), kind=kind, payload=stale_payload
                    )
                return stale_payload
        else:
            return None

        _index_cache[index_url] = _IndexCacheEntry(
            fetched_at=datetime.now(), kind=kind, payload=payload
        )
        return payload


def _score_document(url: str, title: str, text: str, tokens: Sequence[str]) -> int:
    if not tokens:
        return 1

    url_lower = url.lower()
    title_lower = title.lower()
    text_lower = text.lower()

    score = 0
    for token in tokens:
        if token in title_lower:
            score += 25
        if token in url_lower:
            score += 6
        occurrences = text_lower.count(token)
        if occurrences:
            score += 8 + min(occurrences, 20)

    return score


async def _gather_with_limit(
    coros: Sequence[Awaitable[Any]], *, concurrency: int
) -> List[Any]:
    if concurrency <= 1:
        results: List[Any] = []
        for coro in coros:
            results.append(await coro)
        return results

    semaphore = asyncio.Semaphore(concurrency)

    async def _runner(coro: Awaitable[Any]) -> Any:
        async with semaphore:
            return await coro

    return await asyncio.gather(
        *[_runner(coro) for coro in coros], return_exceptions=True
    )


async def _search_via_mkdocs_index(
    site_url: str,
    tokens: Sequence[str],
    client: httpx.AsyncClient,
    *,
    user_agent: str,
    num_results: int,
    allow_network: bool,
) -> Optional[List[Dict[str, str]]]:
    for index_url in _mkdocs_index_candidates(site_url):
        if allow_network:
            docs = await _get_cached_index(
                client,
                index_url,
                user_agent=user_agent,
                kind="mkdocs",
                timeout_seconds=20.0,
            )
        else:
            docs = _get_cached_index_from_memory(index_url, kind="mkdocs")
        if not docs:
            continue

        base_url = _mkdocs_base_from_index_url(index_url)
        scored: List[Tuple[int, Dict[str, str]]] = []
        for doc in docs:
            location = str(doc.get("location") or "")
            url = urljoin(base_url, location)
            if not _matches_site_prefix(url, site_url):
                continue
            title = str(doc.get("title") or "") or _fallback_title_from_url(url)
            text = str(doc.get("text") or "")
            score = _score_document(url, title, text, tokens)
            if score <= 0:
                continue
            snippet = _extract_text_snippet(text, tokens)
            scored.append((score, {"link": url, "title": title, "snippet": snippet}))

        scored.sort(key=lambda item: (-item[0], len(item[1]["link"])))
        organic = [item[1] for item in scored[: max(num_results, 1)]]
        if organic:
            return organic

    return None


def _coerce_sphinx_doc_hits(entry: Any) -> List[Tuple[int, int]]:
    """Return a list of (doc_id, weight) pairs."""
    if not isinstance(entry, list):
        return []
    if not entry:
        return []

    if all(isinstance(item, int) for item in entry):
        return [(item, 1) for item in entry]

    hits: List[Tuple[int, int]] = []
    for item in entry:
        if isinstance(item, int):
            hits.append((item, 1))
            continue
        if isinstance(item, (list, tuple)) and item and isinstance(item[0], int):
            weight = 1
            if len(item) > 1 and isinstance(item[1], int):
                weight = max(item[1], 1)
            hits.append((item[0], weight))
    return hits


async def _search_via_sphinx_index(
    site_url: str,
    tokens: Sequence[str],
    client: httpx.AsyncClient,
    *,
    user_agent: str,
    num_results: int,
    fetch_text: Optional[Callable[[str], Awaitable[str]]],
    fetch_text_concurrency: int,
    allow_network: bool,
) -> Optional[List[Dict[str, str]]]:
    for index_url in _sphinx_index_candidates(site_url):
        if allow_network:
            index = await _get_cached_index(
                client,
                index_url,
                user_agent=user_agent,
                kind="sphinx",
                timeout_seconds=20.0,
            )
        else:
            index = _get_cached_index_from_memory(index_url, kind="sphinx")
        if not isinstance(index, dict):
            continue

        filenames = index.get("filenames")
        titles = index.get("titles")
        terms = index.get("terms")
        titleterms = index.get("titleterms")
        if not (
            isinstance(filenames, list)
            and isinstance(titles, list)
            and isinstance(terms, dict)
        ):
            continue

        base_url = _sphinx_base_from_index_url(index_url)
        scores: Dict[int, int] = {}
        for token in tokens:
            for doc_id, weight in _coerce_sphinx_doc_hits(terms.get(token)):
                scores[doc_id] = scores.get(doc_id, 0) + (10 * weight)
            if isinstance(titleterms, dict):
                for doc_id, weight in _coerce_sphinx_doc_hits(titleterms.get(token)):
                    scores[doc_id] = scores.get(doc_id, 0) + (20 * weight)

        ranked_doc_ids = sorted(scores.items(), key=lambda item: -item[1])
        hits: List[Tuple[int, str]] = []
        for doc_id, _ in ranked_doc_ids:
            if not isinstance(doc_id, int) or doc_id < 0 or doc_id >= len(filenames):
                continue
            url = urljoin(base_url, str(filenames[doc_id]))
            if not _matches_site_prefix(url, site_url):
                continue
            hits.append((doc_id, url))
            if len(hits) >= max(num_results, 1):
                break

        if not hits:
            continue

        urls = [url for _, url in hits]
        snippets_by_url: Dict[str, str] = {url: "" for url in urls}
        if allow_network and fetch_text and tokens:
            texts = await _gather_with_limit(
                [fetch_text(url) for url in urls], concurrency=fetch_text_concurrency
            )
            for url, text in zip(urls, texts):
                if isinstance(text, Exception):
                    continue
                snippets_by_url[url] = _extract_text_snippet(str(text), tokens)
        elif allow_network and tokens:
            metadatas = await asyncio.gather(
                *[
                    _fetch_result_metadata(
                        client, url, user_agent=user_agent, tokens=tokens
                    )
                    for url in urls
                ],
                return_exceptions=True,
            )
            for url, metadata in zip(urls, metadatas):
                if isinstance(metadata, Exception):
                    continue
                snippets_by_url[url] = metadata.get("snippet", "")

        organic: List[Dict[str, str]] = []
        for doc_id, url in hits:
            title = _fallback_title_from_url(url)
            if doc_id < len(titles) and titles[doc_id]:
                title = str(titles[doc_id])
            organic.append(
                {
                    "link": url,
                    "title": title,
                    "snippet": snippets_by_url.get(url, ""),
                }
            )

        if organic:
            return organic

    return None


async def search_site_via_sitemap(
    query: str,
    client: httpx.AsyncClient,
    *,
    user_agent: str,
    num_results: int = 5,
    fetch_text: Optional[Callable[[str], Awaitable[str]]] = None,
    fetch_text_concurrency: int = _DEFAULT_CONTENT_FETCH_CONCURRENCY,
    allow_network: bool = True,
) -> Dict[str, Any]:
    """
    Perform a Serper-free search for `site:` queries.

    Returns a Serper-like payload: {"organic": [{"link","title","snippet"}, ...]}.
    """
    site_url, terms = _parse_site_query(query)
    if not site_url:
        return {"organic": []}

    parsed = urlparse(site_url)
    if not parsed.scheme or not parsed.netloc:
        return {"organic": []}

    origin = f"{parsed.scheme}://{parsed.netloc}"

    tokens = _tokenize_query(terms)

    # 1) Prefer docs-native search indexes when present.
    organic = await _search_via_mkdocs_index(
        site_url,
        tokens,
        client,
        user_agent=user_agent,
        num_results=num_results,
        allow_network=allow_network,
    )
    if not organic:
        organic = await _search_via_sphinx_index(
            site_url,
            tokens,
            client,
            user_agent=user_agent,
            num_results=num_results,
            fetch_text=fetch_text,
            fetch_text_concurrency=fetch_text_concurrency,
            allow_network=allow_network,
        )
    if organic:
        return {"organic": organic}

    # 2) Fallback: sitemap discovery + ranking.
    cached_urls = _get_cached_sitemap_urls_from_memory(origin, allow_stale=False)
    if cached_urls is not None:
        all_urls = cached_urls
    else:
        if not allow_network:
            stale_cached = _get_cached_sitemap_urls_from_memory(
                origin, allow_stale=True
            )
            if stale_cached is None:
                return {"organic": []}
            all_urls = stale_cached
        else:
            lock = _sitemap_locks.setdefault(origin, asyncio.Lock())
            async with lock:
                cached_urls = _get_cached_sitemap_urls_from_memory(
                    origin, allow_stale=False
                )
                if cached_urls is not None:
                    all_urls = cached_urls
                else:
                    loaded = await _load_site_sitemap_urls(
                        client,
                        site_url,
                        user_agent=user_agent,
                        allow_html_fallback=False,
                    )
                    if loaded:
                        _sitemap_cache[origin] = _SitemapCacheEntry(
                            fetched_at=datetime.now(), urls=tuple(loaded)
                        )
                        all_urls = loaded
                    else:
                        stale_cached = _get_cached_sitemap_urls_from_memory(
                            origin, allow_stale=True
                        )
                        if stale_cached is not None:
                            existing = _sitemap_cache.get(origin)
                            if existing and existing.urls:
                                _sitemap_cache[origin] = _SitemapCacheEntry(
                                    fetched_at=datetime.now(), urls=existing.urls
                                )
                            all_urls = stale_cached
                        else:
                            discovered = await _discover_urls_from_html_links(
                                client, site_url, user_agent=user_agent
                            )
                            if not discovered:
                                return {"organic": []}
                            _sitemap_cache[origin] = _SitemapCacheEntry(
                                fetched_at=datetime.now(), urls=tuple(discovered)
                            )
                            all_urls = discovered

    candidates = [u for u in all_urls if _matches_site_prefix(u, site_url)]
    scored = _score_urls(candidates, tokens)

    # Preselect candidates (URL-based), then optionally rescore using page text.
    preselect_limit = min(12, max(6, max(num_results, 1) * 2))
    if scored:
        preselect_urls = [url for _, url in scored[:preselect_limit]]
        url_scores = {url: score for score, url in scored[:preselect_limit]}
    else:
        preselect_urls = sorted(candidates, key=len)[:preselect_limit]
        url_scores = {url: 0 for url in preselect_urls}

    if fetch_text and tokens and preselect_urls:
        texts = await _gather_with_limit(
            [fetch_text(url) for url in preselect_urls],
            concurrency=fetch_text_concurrency,
        )
        rescored: List[Tuple[int, str, str, str]] = []
        for url, text in zip(preselect_urls, texts):
            title = _fallback_title_from_url(url)
            if isinstance(text, Exception):
                rescored.append((url_scores.get(url, 0), url, title, ""))
                continue
            snippet = _extract_text_snippet(str(text), tokens)
            content_score = _score_document(url, title, str(text), tokens)
            total = url_scores.get(url, 0) + content_score
            rescored.append((total, url, title, snippet))

        rescored.sort(key=lambda item: (-item[0], len(item[1])))
        organic = [
            {"link": url, "title": title, "snippet": snippet}
            for _, url, title, snippet in rescored[: max(num_results, 1)]
        ]
        return {"organic": organic}

    top_urls = preselect_urls[: max(num_results, 1)]
    if not top_urls:
        return {"organic": []}

    if not allow_network:
        return {
            "organic": [
                {"link": url, "title": _fallback_title_from_url(url), "snippet": ""}
                for url in top_urls
            ]
        }

    tasks = [
        _fetch_result_metadata(client, url, user_agent=user_agent, tokens=tokens)
        for url in top_urls
    ]
    metadatas = await asyncio.gather(*tasks, return_exceptions=True)

    organic: List[Dict[str, str]] = []
    for url, metadata in zip(top_urls, metadatas):
        if isinstance(metadata, Exception):
            organic.append(
                {
                    "link": url,
                    "title": _fallback_title_from_url(url),
                    "snippet": "",
                }
            )
        else:
            organic.append(
                {
                    "link": url,
                    "title": metadata.get("title", _fallback_title_from_url(url)),
                    "snippet": metadata.get("snippet", ""),
                }
            )

    return {"organic": organic}
