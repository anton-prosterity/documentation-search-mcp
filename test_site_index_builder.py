import json

import httpx
import pytest

from documentation_search_enhanced.site_index_builder import (
    SiteIndexBuildSettings,
    build_site_index_file,
)
from documentation_search_enhanced import site_search


@pytest.mark.asyncio
async def test_build_site_index_file_writes_indexes_and_missing_sitemaps(
    tmp_path, monkeypatch
):
    mkdocs_site = "https://mkdocs.example.com/docs/"
    sphinx_site = "https://sphinx.example.com/"
    noindex_site = "https://noindex.example.com/"

    mkdocs_index_url = "https://mkdocs.example.com/docs/search/search_index.json"
    sphinx_index_url = "https://sphinx.example.com/searchindex.js"

    mkdocs_blob = json.dumps(
        {
            "docs": [
                {
                    "location": "reference/authentication/",
                    "title": "Authentication",
                    "text": "Authentication middleware reference and examples.",
                }
            ]
        }
    ).encode("utf-8")
    sphinx_blob = (
        'Search.setIndex({"filenames":["ref/auth.html"],'
        '"titles":["Authentication"],'
        '"terms":{"authentication":[0]}})'
    ).encode("utf-8")

    async def fake_fetch_bytes(
        client: httpx.AsyncClient,
        url: str,
        *,
        user_agent: str,
        timeout_seconds: float,
    ):
        if url == mkdocs_index_url:
            return mkdocs_blob
        if url == sphinx_index_url:
            return sphinx_blob
        return None

    calls = {"sitemaps": 0}

    async def fake_load_site_sitemap_urls(
        client: httpx.AsyncClient, site_url: str, *, user_agent: str
    ):
        calls["sitemaps"] += 1
        assert site_url == noindex_site
        return [f"{noindex_site}guide/authentication/"]

    monkeypatch.setattr(site_search, "_fetch_bytes", fake_fetch_bytes)
    monkeypatch.setattr(
        site_search, "_load_site_sitemap_urls", fake_load_site_sitemap_urls
    )

    output = tmp_path / "docs_site_index.json"
    result = await build_site_index_file(
        {
            "mkdocs": mkdocs_site,
            "sphinx": sphinx_site,
            "noindex": noindex_site,
        },
        output_path=str(output),
        gzip_output=False,
        settings=SiteIndexBuildSettings(
            user_agent="tests",
            sitemap_mode="missing",
            max_sitemap_urls=100,
            max_concurrent_sites=2,
        ),
    )

    assert result["status"] == "ok"
    assert result["indexed_libraries"] == 3
    assert calls["sitemaps"] == 1

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert mkdocs_index_url in payload["indexes"]
    assert sphinx_index_url in payload["indexes"]
    assert payload["sitemaps"]["https://noindex.example.com"]["urls"] == [
        f"{noindex_site}guide/authentication/"
    ]
