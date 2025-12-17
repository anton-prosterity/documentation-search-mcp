#!/usr/bin/env python3
"""Build a preindexed docs site index for Serper-free search.

This module is used by CI to generate `docs_site_index.json` (+ optional `.gz`) assets
that are published to GitHub Releases and auto-downloaded by the server at startup.
"""

from __future__ import annotations

import asyncio
import argparse
import gzip
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Optional
from urllib.parse import urlparse

import httpx

from . import site_search


@dataclass(frozen=True)
class SiteIndexBuildSettings:
    user_agent: str
    max_concurrent_sites: int = 5
    sitemap_mode: str = "missing"  # none|missing|all
    max_sitemap_urls: int = 5_000
    timeout_seconds: float = 60.0


def load_docs_urls_from_config(config_path: str) -> Dict[str, str]:
    if not config_path:
        raise ValueError("config_path must be non-empty")
    with open(config_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    raw = data.get("docs_urls", {})
    if not isinstance(raw, dict):
        return {}

    docs_urls: Dict[str, str] = {}
    for name, value in raw.items():
        if not isinstance(name, str):
            continue
        if isinstance(value, dict):
            url = str(value.get("url") or "").strip()
        else:
            url = str(value or "").strip()
        if url:
            docs_urls[name] = url
    return docs_urls


def _parse_libraries(value: Optional[str]) -> Optional[list[str]]:
    if not value:
        return None
    parts = [part.strip() for part in value.split(",")]
    libraries = [part for part in parts if part]
    return libraries or None


def _origin_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


async def build_site_index_file(
    docs_urls: Mapping[str, str],
    *,
    output_path: str,
    gzip_output: bool,
    settings: SiteIndexBuildSettings,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    if not output_path:
        raise ValueError("output_path must be non-empty")

    if settings.sitemap_mode not in {"none", "missing", "all"}:
        raise ValueError("sitemap_mode must be one of: none, missing, all")

    site_search._sitemap_cache.clear()
    site_search._sitemap_locks.clear()
    site_search._index_cache.clear()
    site_search._index_locks.clear()

    original_max_sitemap_urls = getattr(site_search, "_MAX_SITEMAP_URLS", None)
    if settings.max_sitemap_urls and settings.max_sitemap_urls > 0:
        site_search._MAX_SITEMAP_URLS = int(settings.max_sitemap_urls)

    created_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(settings.timeout_seconds))

    try:
        concurrency = max(1, min(int(settings.max_concurrent_sites), 20))
        semaphore = asyncio.Semaphore(concurrency)

        results: list[dict[str, Any]] = []

        async def run_one(library: str, url: str) -> None:
            async with semaphore:
                summary = await site_search.preindex_site(
                    url,
                    client,
                    user_agent=settings.user_agent,
                    include_sitemap=False,
                )

                has_index = bool(
                    summary.get("mkdocs_index") or summary.get("sphinx_index")
                )
                include_sitemap = settings.sitemap_mode == "all" or (
                    settings.sitemap_mode == "missing" and not has_index
                )
                if include_sitemap:
                    origin = summary.get("origin") or _origin_from_url(url)
                    try:
                        urls = await site_search._load_site_sitemap_urls(  # type: ignore[attr-defined]
                            client,
                            url,
                            user_agent=settings.user_agent,
                        )
                    except Exception as e:
                        summary.setdefault("errors", []).append(f"sitemap:{e}")
                    else:
                        if origin and urls:
                            site_search._sitemap_cache[origin] = (
                                site_search._SitemapCacheEntry(  # type: ignore[attr-defined]
                                    fetched_at=datetime.now(),
                                    urls=tuple(urls),
                                )
                            )
                            summary["sitemap"] = {"urls": len(urls)}

                summary["library"] = library
                results.append(summary)

        tasks = [
            run_one(library, url)
            for library, url in sorted(docs_urls.items(), key=lambda item: item[0])
            if url
        ]
        if tasks:
            await asyncio.gather(*tasks)

        site_search.save_preindexed_state(output_path)

        gz_path: Optional[str] = None
        if gzip_output:
            gz_path = f"{output_path}.gz"
            with open(output_path, "rb") as fh:
                blob = fh.read()
            with gzip.open(gz_path, "wb", compresslevel=9) as fh:
                fh.write(blob)

        indexed_sites = sum(
            1
            for summary in results
            if summary.get("mkdocs_index")
            or summary.get("sphinx_index")
            or summary.get("sitemap")
        )

        return {
            "status": "ok" if indexed_sites else "error",
            "output_path": output_path,
            "gzip_path": gz_path,
            "total_libraries": len(docs_urls),
            "indexed_libraries": indexed_sites,
            "results": sorted(results, key=lambda item: str(item.get("library") or "")),
        }
    finally:
        if original_max_sitemap_urls is not None:
            site_search._MAX_SITEMAP_URLS = original_max_sitemap_urls
        if created_client:
            await client.aclose()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build docs_site_index.json for releases."
    )
    parser.add_argument(
        "--config",
        default=os.path.join("src", "documentation_search_enhanced", "config.json"),
        help="Path to config.json (default: bundled src config).",
    )
    parser.add_argument(
        "--output",
        default="docs_site_index.json",
        help="Path to write the index JSON (default: docs_site_index.json).",
    )
    parser.add_argument(
        "--gzip",
        action="store_true",
        help="Also write a .gz next to the JSON file.",
    )
    parser.add_argument(
        "--libraries",
        default=None,
        help="Comma-separated list of libraries to index (default: all).",
    )
    parser.add_argument(
        "--sitemap",
        choices=("none", "missing", "all"),
        default="missing",
        help="Whether to include sitemap URLs: none, missing, or all (default: missing).",
    )
    parser.add_argument(
        "--max-sitemap-urls",
        type=int,
        default=5_000,
        help="Max sitemap URLs per site when included (default: 5000).",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=5,
        help="Max concurrent sites to index (default: 5).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=60.0,
        help="HTTP timeout (default: 60s).",
    )
    parser.add_argument(
        "--user-agent",
        default="documentation-search-enhanced/index-builder",
        help="User-Agent header to use for fetches.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)

    docs_urls = load_docs_urls_from_config(args.config)
    libraries = _parse_libraries(args.libraries)
    if libraries:
        docs_urls = {lib: docs_urls[lib] for lib in libraries if lib in docs_urls}

    settings = SiteIndexBuildSettings(
        user_agent=args.user_agent,
        max_concurrent_sites=args.max_concurrency,
        sitemap_mode=args.sitemap,
        max_sitemap_urls=args.max_sitemap_urls,
        timeout_seconds=args.timeout_seconds,
    )

    if not docs_urls:
        print("No documentation sources found to index.", file=sys.stderr)
        return 2

    result = asyncio.run(
        build_site_index_file(
            docs_urls,
            output_path=args.output,
            gzip_output=bool(args.gzip),
            settings=settings,
        )
    )
    print(json.dumps(result, indent=2, sort_keys=True), file=sys.stderr)
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
