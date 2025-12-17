#!/usr/bin/env python3
"""Download and manage the prebuilt docs site index.

The server can operate without Serper by using docs-native search indexes (MkDocs/Sphinx)
and/or a prebuilt index file. This module implements an optional auto-download flow
from GitHub Releases to keep that prebuilt index up to date without requiring users
to run any indexing commands.
"""

from __future__ import annotations

import gzip
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

import httpx


DEFAULT_RELEASE_REPO = "anton-prosterity/documentation-search-mcp"
DEFAULT_RELEASE_ASSET_BASENAME = "docs_site_index.json"
DEFAULT_RELEASE_URLS = (
    f"https://github.com/{DEFAULT_RELEASE_REPO}/releases/latest/download/{DEFAULT_RELEASE_ASSET_BASENAME}.gz",
    f"https://github.com/{DEFAULT_RELEASE_REPO}/releases/latest/download/{DEFAULT_RELEASE_ASSET_BASENAME}",
)


@dataclass(frozen=True)
class SiteIndexDownloadSettings:
    path: str
    urls: Tuple[str, ...] = DEFAULT_RELEASE_URLS
    auto_download: bool = True
    max_age_hours: int = 24 * 7


def _parse_bool(value: Optional[str], *, default: bool) -> bool:
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_int(value: Optional[str], *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def _split_urls(value: Optional[str]) -> Tuple[str, ...]:
    if not value:
        return ()
    parts = [part.strip() for part in value.split(",")]
    return tuple(part for part in parts if part)


def _default_cache_dir() -> Path:
    xdg_cache = os.getenv("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache)
    home = os.path.expanduser("~")
    if home and home != "~":
        return Path(home) / ".cache"
    return Path(os.getcwd())


def default_site_index_path(*, cwd: Optional[str] = None) -> str:
    """Choose a reasonable default path for the prebuilt index file."""
    cwd_path = Path(cwd or os.getcwd()) / ".docs_site_index.json"
    if cwd_path.exists():
        return str(cwd_path)

    cache_dir = _default_cache_dir() / "documentation-search-enhanced"
    return str(cache_dir / "docs_site_index.json")


def load_site_index_settings_from_env(
    *, cwd: Optional[str] = None
) -> SiteIndexDownloadSettings:
    """Load site index settings from environment variables."""
    path = os.getenv("DOCS_SITE_INDEX_PATH") or default_site_index_path(cwd=cwd)

    urls = _split_urls(os.getenv("DOCS_SITE_INDEX_URLS"))
    if not urls:
        url = os.getenv("DOCS_SITE_INDEX_URL")
        urls = (url.strip(),) if url and url.strip() else DEFAULT_RELEASE_URLS

    auto_download = _parse_bool(
        os.getenv("DOCS_SITE_INDEX_AUTO_DOWNLOAD"), default=True
    )
    max_age_hours = _parse_int(
        os.getenv("DOCS_SITE_INDEX_MAX_AGE_HOURS"), default=24 * 7
    )

    return SiteIndexDownloadSettings(
        path=path,
        urls=urls,
        auto_download=auto_download,
        max_age_hours=max_age_hours,
    )


def should_download_site_index(path: str, *, max_age_hours: int) -> bool:
    """Return True when the on-disk index is missing or older than max_age_hours."""
    if not path:
        return False
    target = Path(path)
    if not target.exists():
        return True

    if max_age_hours <= 0:
        return True

    try:
        mtime = datetime.fromtimestamp(target.stat().st_mtime)
    except Exception:
        return True
    return datetime.now() - mtime > timedelta(hours=max_age_hours)


def _maybe_decompress_gzip(blob: bytes) -> bytes:
    if len(blob) >= 2 and blob[0] == 0x1F and blob[1] == 0x8B:
        return gzip.decompress(blob)
    return blob


def _validate_index_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Index file must be a JSON object")
    schema_version = payload.get("schema_version")
    if schema_version != 1:
        raise ValueError(f"Unsupported index schema_version: {schema_version!r}")
    if "indexes" not in payload and "sitemaps" not in payload:
        raise ValueError("Index file missing expected keys")
    return payload


async def download_site_index(
    client: httpx.AsyncClient,
    *,
    urls: Sequence[str],
    dest_path: str,
    user_agent: str,
    timeout_seconds: float = 60.0,
) -> Dict[str, Any]:
    """Download the latest index from the first working URL and save it to dest_path."""
    if not dest_path:
        return {"status": "error", "error": "dest_path is empty"}

    errors: list[str] = []
    headers = {"User-Agent": user_agent}

    for url in urls:
        try:
            response = await client.get(
                url,
                headers=headers,
                timeout=httpx.Timeout(timeout_seconds),
                follow_redirects=True,
            )
            if response.status_code == 404:
                errors.append(f"{url}: 404")
                continue
            response.raise_for_status()

            blob = _maybe_decompress_gzip(response.content)
            payload = json.loads(blob.decode("utf-8"))
            _validate_index_payload(payload)

            target = Path(dest_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = target.with_suffix(target.suffix + ".tmp")
            tmp_path.write_bytes(blob)
            tmp_path.replace(target)

            return {
                "status": "downloaded",
                "url": url,
                "bytes": len(blob),
            }
        except Exception as e:
            errors.append(f"{url}: {e}")

    return {"status": "error", "errors": errors}


async def ensure_site_index_file(
    client: httpx.AsyncClient,
    *,
    settings: SiteIndexDownloadSettings,
    user_agent: str,
) -> Dict[str, Any]:
    """Ensure a reasonably fresh site index exists on disk (download if needed)."""
    if not settings.auto_download:
        return {
            "status": "skipped",
            "reason": "auto_download disabled",
            "path": settings.path,
        }

    if not should_download_site_index(
        settings.path, max_age_hours=settings.max_age_hours
    ):
        return {"status": "ok", "reason": "up_to_date", "path": settings.path}

    result = await download_site_index(
        client,
        urls=settings.urls,
        dest_path=settings.path,
        user_agent=user_agent,
    )
    result["path"] = settings.path
    return result
