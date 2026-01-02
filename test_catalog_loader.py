import json

import httpx

from documentation_search_enhanced import catalog_loader


def test_load_catalog_payload_uses_cache_when_configured(tmp_path):
    payload = {
        "schema_version": 1,
        "docs_urls": {"fastapi": {"url": "https://fastapi.tiangolo.com/"}},
    }
    dest_path = tmp_path / "docs_catalog.json"
    dest_path.write_text(json.dumps(payload), encoding="utf-8")

    settings = catalog_loader.CatalogDownloadSettings(
        path=str(dest_path),
        urls=(),
        auto_download=False,
        max_age_hours=24,
        etag_path=None,
        allow_cache=True,
    )

    loaded, info = catalog_loader.load_catalog_payload(settings, user_agent="tests")

    assert loaded["docs_urls"]["fastapi"]["url"] == "https://fastapi.tiangolo.com/"
    assert info["status"] == "cached"


def test_load_catalog_payload_downloads_and_writes(tmp_path):
    payload = {
        "schema_version": 1,
        "docs_urls": {"react": {"url": "https://react.dev/"}},
    }
    url = "https://example.com/docs_catalog.json"

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == url
        return httpx.Response(200, json=payload, headers={"ETag": "W/\"abc\""})

    dest_path = tmp_path / "docs_catalog.json"
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    settings = catalog_loader.CatalogDownloadSettings(
        path=str(dest_path),
        urls=(url,),
        auto_download=True,
        max_age_hours=0,
        etag_path=str(dest_path) + ".etag",
        allow_cache=True,
    )

    loaded, info = catalog_loader.load_catalog_payload(
        settings, user_agent="tests", client=client
    )

    assert loaded["docs_urls"]["react"]["url"] == "https://react.dev/"
    assert info["status"] == "downloaded"
    assert dest_path.exists()
    assert (tmp_path / "docs_catalog.json.etag").exists()


def test_load_catalog_payload_uses_cache_on_not_modified(tmp_path):
    payload = {
        "schema_version": 1,
        "docs_urls": {"python": {"url": "https://docs.python.org/3/"}},
    }
    url = "https://example.com/docs_catalog.json"

    dest_path = tmp_path / "docs_catalog.json"
    dest_path.write_text(json.dumps(payload), encoding="utf-8")
    etag_path = tmp_path / "docs_catalog.json.etag"
    etag_path.write_text("W/\"abc\"", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("If-None-Match") == "W/\"abc\""
        return httpx.Response(304)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    settings = catalog_loader.CatalogDownloadSettings(
        path=str(dest_path),
        urls=(url,),
        auto_download=True,
        max_age_hours=0,
        etag_path=str(etag_path),
        allow_cache=True,
    )

    loaded, info = catalog_loader.load_catalog_payload(
        settings, user_agent="tests", client=client
    )

    assert loaded["docs_urls"]["python"]["url"] == "https://docs.python.org/3/"
    assert info["status"] == "not_modified"
