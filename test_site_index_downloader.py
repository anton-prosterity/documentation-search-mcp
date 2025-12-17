import gzip
import json
import os
import time

import httpx
import pytest

from documentation_search_enhanced import site_index_downloader


@pytest.mark.asyncio
async def test_download_site_index_downloads_and_writes_decompressed_json(tmp_path):
    payload = {
        "schema_version": 1,
        "generated_at": "2025-01-01T00:00:00",
        "sitemaps": {},
        "indexes": {},
    }
    gz_blob = gzip.compress(json.dumps(payload).encode("utf-8"))
    url = "https://example.com/docs_site_index.json.gz"

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == url
        return httpx.Response(200, content=gz_blob)

    dest_path = tmp_path / "docs_site_index.json"
    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        result = await site_index_downloader.download_site_index(
            client,
            urls=(url,),
            dest_path=str(dest_path),
            user_agent="tests",
        )

    assert result["status"] == "downloaded"
    assert dest_path.exists()
    stored = json.loads(dest_path.read_text(encoding="utf-8"))
    assert stored["schema_version"] == 1


@pytest.mark.asyncio
async def test_download_site_index_falls_back_to_second_url_on_404(tmp_path):
    payload = {
        "schema_version": 1,
        "generated_at": "2025-01-01T00:00:00",
        "sitemaps": {},
        "indexes": {},
    }
    blob = json.dumps(payload).encode("utf-8")
    first = "https://example.com/missing.json.gz"
    second = "https://example.com/docs_site_index.json"

    async def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == first:
            return httpx.Response(404)
        assert str(request.url) == second
        return httpx.Response(200, content=blob)

    dest_path = tmp_path / "docs_site_index.json"
    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        result = await site_index_downloader.download_site_index(
            client,
            urls=(first, second),
            dest_path=str(dest_path),
            user_agent="tests",
        )

    assert result["status"] == "downloaded"
    assert result["url"] == second
    assert dest_path.exists()


@pytest.mark.asyncio
async def test_ensure_site_index_file_skips_when_up_to_date(tmp_path):
    dest_path = tmp_path / "docs_site_index.json"
    dest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "2025-01-01T00:00:00",
                "sitemaps": {},
                "indexes": {},
            }
        ),
        encoding="utf-8",
    )
    now = time.time()
    os.utime(dest_path, (now, now))

    async def handler(_: httpx.Request) -> httpx.Response:
        raise AssertionError("Network should not be called when index is up to date")

    transport = httpx.MockTransport(handler)
    settings = site_index_downloader.SiteIndexDownloadSettings(
        path=str(dest_path),
        urls=("https://example.com/should-not-fetch.json",),
        auto_download=True,
        max_age_hours=24 * 7,
    )

    async with httpx.AsyncClient(transport=transport) as client:
        result = await site_index_downloader.ensure_site_index_file(
            client,
            settings=settings,
            user_agent="tests",
        )

    assert result["status"] == "ok"
    assert result["path"] == str(dest_path)
