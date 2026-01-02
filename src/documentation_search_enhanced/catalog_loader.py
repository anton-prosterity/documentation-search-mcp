"""
Load and cache a remote documentation catalog.

The catalog is a JSON payload that provides docs_urls (and optional categories)
so the server can avoid hardcoding library definitions locally.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

import httpx


DEFAULT_MAX_AGE_HOURS = 24
DEFAULT_USER_AGENT = "docs-catalog/1.0"


@dataclass(frozen=True)
class CatalogDownloadSettings:
    path: str
    urls: Tuple[str, ...] = ()
    auto_download: bool = False
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS
    etag_path: Optional[str] = None
    allow_cache: bool = False


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


def default_catalog_path(*, cwd: Optional[str] = None) -> str:
    cwd_path = Path(cwd or os.getcwd()) / ".docs_catalog.json"
    if cwd_path.exists():
        return str(cwd_path)
    cache_dir = _default_cache_dir() / "documentation-search-enhanced"
    return str(cache_dir / "docs_catalog.json")


def load_catalog_settings_from_env(
    *, cwd: Optional[str] = None
) -> CatalogDownloadSettings:
    explicit_path = os.getenv("DOCS_CONFIG_PATH")
    path = explicit_path or default_catalog_path(cwd=cwd)

    urls = _split_urls(os.getenv("DOCS_CONFIG_URLS"))
    if not urls:
        url = os.getenv("DOCS_CONFIG_URL")
        urls = (url.strip(),) if url and url.strip() else ()

    auto_download = _parse_bool(
        os.getenv("DOCS_CONFIG_AUTO_DOWNLOAD"), default=bool(urls)
    )
    max_age_hours = _parse_int(
        os.getenv("DOCS_CONFIG_MAX_AGE_HOURS"), default=DEFAULT_MAX_AGE_HOURS
    )

    allow_cache = bool(explicit_path or urls)
    etag_path = os.getenv("DOCS_CONFIG_ETAG_PATH") or (
        f"{path}.etag" if allow_cache else None
    )

    return CatalogDownloadSettings(
        path=path,
        urls=urls,
        auto_download=auto_download,
        max_age_hours=max_age_hours,
        etag_path=etag_path,
        allow_cache=allow_cache,
    )


def should_download_catalog(path: str, *, max_age_hours: int) -> bool:
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


def _read_etag(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    target = Path(path)
    if not target.exists():
        return None
    value = target.read_text(encoding="utf-8").strip()
    return value or None


def _write_etag(path: Optional[str], value: Optional[str]) -> None:
    if not path or not value:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def _load_cached_payload(path: str) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    target = Path(path)
    if not target.exists():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return None
    try:
        return _validate_catalog_payload(payload)
    except ValueError:
        return None


def _validate_catalog_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Catalog payload must be a JSON object")
    schema_version = payload.get("schema_version")
    if schema_version is not None and schema_version != 1:
        raise ValueError(f"Unsupported catalog schema_version: {schema_version!r}")
    docs_urls = payload.get("docs_urls")
    if not isinstance(docs_urls, dict):
        raise ValueError("Catalog payload missing docs_urls")
    categories = payload.get("categories")
    if categories is not None and not isinstance(categories, dict):
        raise ValueError("Catalog categories must be an object when provided")
    return payload


def download_catalog(
    *,
    urls: Sequence[str],
    dest_path: str,
    user_agent: str,
    timeout_seconds: float = 10.0,
    etag_path: Optional[str] = None,
    client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    if not dest_path:
        return {"status": "error", "error": "dest_path is empty"}

    headers = {"User-Agent": user_agent}
    etag = _read_etag(etag_path)
    if etag:
        headers["If-None-Match"] = etag

    errors: list[str] = []
    close_client = False
    if client is None:
        client = httpx.Client(timeout=timeout_seconds)
        close_client = True

    try:
        for url in urls:
            try:
                response = client.get(url, headers=headers, follow_redirects=True)
                if response.status_code == 304:
                    return {"status": "not_modified", "url": url}
                if response.status_code == 404:
                    errors.append(f"{url}: 404")
                    continue
                response.raise_for_status()

                payload = json.loads(response.text)
                payload = _validate_catalog_payload(payload)

                target = Path(dest_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = target.with_suffix(target.suffix + ".tmp")
                tmp_path.write_text(json.dumps(payload), encoding="utf-8")
                tmp_path.replace(target)

                _write_etag(etag_path, response.headers.get("ETag"))

                return {
                    "status": "downloaded",
                    "url": url,
                    "bytes": len(response.content),
                    "payload": payload,
                }
            except Exception as e:
                errors.append(f"{url}: {e}")
    finally:
        if close_client:
            client.close()

    return {"status": "error", "errors": errors}


def load_catalog_payload(
    settings: CatalogDownloadSettings,
    *,
    user_agent: Optional[str] = None,
    timeout_seconds: float = 10.0,
    client: Optional[httpx.Client] = None,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    if not settings.allow_cache and not settings.urls:
        return None, {"status": "skipped", "reason": "not_configured"}

    payload = _load_cached_payload(settings.path) if settings.allow_cache else None

    if settings.auto_download and settings.urls and should_download_catalog(
        settings.path, max_age_hours=settings.max_age_hours
    ):
        result = download_catalog(
            urls=settings.urls,
            dest_path=settings.path,
            user_agent=user_agent or DEFAULT_USER_AGENT,
            timeout_seconds=timeout_seconds,
            etag_path=settings.etag_path,
            client=client,
        )
        status = result.get("status")
        if status == "downloaded":
            payload = result.get("payload")
        elif status == "not_modified":
            pass
        elif status == "error":
            pass
        result["path"] = settings.path
        return payload, result

    if payload:
        return payload, {"status": "cached", "path": settings.path}
    return None, {"status": "skipped", "reason": "no_cache"}


def merge_catalog_config(
    base_config: Dict[str, Any],
    catalog_payload: Dict[str, Any],
) -> Dict[str, Any]:
    merged = dict(base_config)
    docs_urls = catalog_payload.get("docs_urls")
    if isinstance(docs_urls, dict):
        merged["docs_urls"] = docs_urls
    if "categories" in catalog_payload:
        categories = catalog_payload.get("categories")
        merged["categories"] = categories if isinstance(categories, dict) else {}
    return merged
