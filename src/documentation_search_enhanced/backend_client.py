"""Client for the external docs backend (e.g., Cloudflare Worker)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass(frozen=True)
class BackendConfig:
    base_url: str
    api_key: Optional[str] = None
    timeout_seconds: float = 12.0


def load_backend_config() -> Optional[BackendConfig]:
    base_url = os.getenv("DOCS_BACKEND_URL") or os.getenv("DOCS_API_URL")
    if not base_url:
        return None
    base_url = base_url.rstrip("/")
    api_key = os.getenv("DOCS_BACKEND_API_KEY") or os.getenv("DOCS_API_KEY")
    timeout = float(os.getenv("DOCS_BACKEND_TIMEOUT_SECONDS", "12"))
    return BackendConfig(
        base_url=base_url,
        api_key=api_key,
        timeout_seconds=timeout,
    )


def _build_headers(config: BackendConfig) -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    return headers


async def backend_search(
    client: httpx.AsyncClient,
    config: BackendConfig,
    *,
    query: str,
    library: Optional[str],
    version: Optional[str],
    limit: int,
    mode: Optional[str] = None,
    context: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {
        "query": query,
        "limit": limit,
    }
    if library:
        payload["library"] = library
    if version:
        payload["version"] = version
    if mode:
        payload["mode"] = mode
    if context:
        payload["context"] = context

    url = f"{config.base_url}/search"
    try:
        response = await client.post(
            url,
            json=payload,
            headers=_build_headers(config),
            timeout=config.timeout_seconds,
        )
        if response.status_code >= 400:
            return None
        return response.json()
    except Exception:
        return None


async def backend_get_docs(
    client: httpx.AsyncClient,
    config: BackendConfig,
    *,
    library: str,
    version: str,
    topic: Optional[str],
    limit: int,
) -> Optional[Dict[str, Any]]:
    url = f"{config.base_url}/docs/{library}/{version}"
    params: Dict[str, Any] = {"limit": limit}
    if topic:
        params["topic"] = topic

    try:
        response = await client.get(
            url,
            params=params,
            headers=_build_headers(config),
            timeout=config.timeout_seconds,
        )
        if response.status_code >= 400:
            return None
        return response.json()
    except Exception:
        return None
