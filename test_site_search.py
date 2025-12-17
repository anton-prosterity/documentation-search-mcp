from datetime import datetime, timedelta

import httpx
import pytest

from documentation_search_enhanced import site_search


@pytest.mark.asyncio
async def test_search_site_via_sitemap_ranks_and_caches(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = {"loads": 0}

    async def fake_search_via_mkdocs_index(*args, **kwargs):
        return None

    async def fake_search_via_sphinx_index(*args, **kwargs):
        return None

    async def fake_load_site_sitemap_urls(
        client: httpx.AsyncClient,
        site_url: str,
        *,
        user_agent: str,
        allow_html_fallback: bool = True,
    ):
        _ = allow_html_fallback
        calls["loads"] += 1
        return [
            "https://docs.example.com/reference/authentication/middleware/",
            "https://docs.example.com/reference/authentication/",
            "https://docs.example.com/reference/middleware/",
            "https://docs.example.com/reference/intro/",
            "https://docs.example.com/guide/authentication/middleware/",
            "https://other.example.com/reference/authentication/middleware/",
        ]

    async def fake_fetch_result_metadata(
        client: httpx.AsyncClient, url: str, *, user_agent: str, tokens
    ):
        return {"title": f"Title {url}", "snippet": "Example snippet"}

    monkeypatch.setattr(
        site_search, "_search_via_mkdocs_index", fake_search_via_mkdocs_index
    )
    monkeypatch.setattr(
        site_search, "_search_via_sphinx_index", fake_search_via_sphinx_index
    )
    monkeypatch.setattr(
        site_search, "_load_site_sitemap_urls", fake_load_site_sitemap_urls
    )
    monkeypatch.setattr(
        site_search, "_fetch_result_metadata", fake_fetch_result_metadata
    )
    site_search._sitemap_cache.clear()
    site_search._sitemap_locks.clear()
    site_search._index_cache.clear()
    site_search._index_locks.clear()

    query = "site:https://docs.example.com/reference/ authentication middleware"

    async with httpx.AsyncClient() as client:
        result = await site_search.search_site_via_sitemap(
            query, client, user_agent="tests", num_results=3
        )
        links = [item["link"] for item in result["organic"]]
        assert (
            links[0] == "https://docs.example.com/reference/authentication/middleware/"
        )
        assert sorted(links[1:]) == sorted(
            [
                "https://docs.example.com/reference/authentication/",
                "https://docs.example.com/reference/middleware/",
            ]
        )
        assert calls["loads"] == 1

        # Second call should hit in-memory sitemap cache.
        _ = await site_search.search_site_via_sitemap(
            query, client, user_agent="tests", num_results=3
        )
        assert calls["loads"] == 1


@pytest.mark.asyncio
async def test_search_site_via_sitemap_requires_site():
    async with httpx.AsyncClient() as client:
        result = await site_search.search_site_via_sitemap(
            "authentication middleware", client, user_agent="tests", num_results=3
        )
    assert result == {"organic": []}


@pytest.mark.asyncio
async def test_load_site_sitemap_urls_falls_back_to_html_links(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_discover_sitemaps_from_robots(*_args, **_kwargs):
        return []

    async def fake_fetch_bytes(
        client: httpx.AsyncClient,
        url: str,
        *,
        user_agent: str,
        timeout_seconds: float,
    ):
        _ = client, user_agent, timeout_seconds
        if "sitemap" in url:
            return None
        if url == "https://react.dev/reference/react":
            return b'<html><body><a href="/reference/react/components">Components</a></body></html>'
        return None

    monkeypatch.setattr(
        site_search,
        "_discover_sitemaps_from_robots",
        fake_discover_sitemaps_from_robots,
    )
    monkeypatch.setattr(site_search, "_fetch_bytes", fake_fetch_bytes)

    async with httpx.AsyncClient() as client:
        urls = await site_search._load_site_sitemap_urls(
            client, "https://react.dev/reference/react", user_agent="tests"
        )

    assert "https://react.dev/reference/react/components" in urls


@pytest.mark.asyncio
async def test_search_site_prefers_mkdocs_index(monkeypatch: pytest.MonkeyPatch):
    async def fake_get_cached_index(
        client: httpx.AsyncClient,
        index_url: str,
        *,
        user_agent: str,
        kind: str,
        timeout_seconds: float,
    ):
        assert kind == "mkdocs"
        return (
            {
                "location": "reference/authentication/middleware/",
                "title": "Auth Middleware",
                "text": "Authentication middleware reference and examples.",
            },
            {
                "location": "reference/intro/",
                "title": "Intro",
                "text": "Welcome to the docs.",
            },
        )

    async def should_not_call_sitemap(*args, **kwargs):
        raise AssertionError("Sitemap fallback should not be called when index exists")

    monkeypatch.setattr(
        site_search,
        "_mkdocs_index_candidates",
        lambda _: ["https://docs.example.com/search/search_index.json"],
    )
    monkeypatch.setattr(
        site_search,
        "_mkdocs_base_from_index_url",
        lambda _: "https://docs.example.com/",
    )
    monkeypatch.setattr(site_search, "_get_cached_index", fake_get_cached_index)
    monkeypatch.setattr(site_search, "_load_site_sitemap_urls", should_not_call_sitemap)

    async with httpx.AsyncClient() as client:
        result = await site_search.search_site_via_sitemap(
            "site:https://docs.example.com/reference/ authentication middleware",
            client,
            user_agent="tests",
            num_results=2,
        )

    assert [item["link"] for item in result["organic"]] == [
        "https://docs.example.com/reference/authentication/middleware/",
    ]


@pytest.mark.asyncio
async def test_search_site_uses_sphinx_index_and_snippets(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_get_cached_index(
        client: httpx.AsyncClient,
        index_url: str,
        *,
        user_agent: str,
        kind: str,
        timeout_seconds: float,
    ):
        assert kind == "sphinx"
        return {
            "filenames": ["ref/auth.html", "ref/middleware.html"],
            "titles": ["Authentication", "Middleware"],
            "terms": {
                "authentication": [0],
                "middleware": [1],
            },
        }

    async def fake_fetch_text(url: str) -> str:
        return f"{url} Authentication middleware details and examples."

    async def fake_search_via_mkdocs_index(*args, **kwargs):
        return None

    monkeypatch.setattr(
        site_search, "_search_via_mkdocs_index", fake_search_via_mkdocs_index
    )
    monkeypatch.setattr(
        site_search,
        "_sphinx_index_candidates",
        lambda _: ["https://docs.example.com/searchindex.js"],
    )
    monkeypatch.setattr(
        site_search,
        "_sphinx_base_from_index_url",
        lambda _: "https://docs.example.com/",
    )
    monkeypatch.setattr(site_search, "_get_cached_index", fake_get_cached_index)

    async with httpx.AsyncClient() as client:
        result = await site_search.search_site_via_sitemap(
            "site:https://docs.example.com/ref/ authentication middleware",
            client,
            user_agent="tests",
            num_results=2,
            fetch_text=fake_fetch_text,
        )

    assert result["organic"][0]["link"] == "https://docs.example.com/ref/auth.html"
    assert result["organic"][0]["title"] == "Authentication"
    assert "authentication" in result["organic"][0]["snippet"].lower()


@pytest.mark.asyncio
async def test_preindexed_state_roundtrip_offline(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    site_search._sitemap_cache.clear()
    site_search._sitemap_locks.clear()
    site_search._index_cache.clear()
    site_search._index_locks.clear()

    origin = "https://docs.example.com"
    site_search._sitemap_cache[origin] = site_search._SitemapCacheEntry(
        fetched_at=datetime.now() - timedelta(days=365),
        urls=(
            "https://docs.example.com/reference/authentication/middleware/",
            "https://docs.example.com/reference/authentication/",
        ),
    )

    persist_path = tmp_path / "preindex.json"
    site_search.save_preindexed_state(str(persist_path))

    site_search._sitemap_cache.clear()
    assert site_search.load_preindexed_state(str(persist_path)) is True

    async def should_not_fetch(*args, **kwargs):
        raise AssertionError("Should not fetch sitemap in offline mode when cached")

    monkeypatch.setattr(site_search, "_load_site_sitemap_urls", should_not_fetch)

    async with httpx.AsyncClient() as client:
        result = await site_search.search_site_via_sitemap(
            "site:https://docs.example.com/reference/ authentication middleware",
            client,
            user_agent="tests",
            num_results=2,
            allow_network=False,
        )

    assert [item["link"] for item in result["organic"]] == [
        "https://docs.example.com/reference/authentication/middleware/",
        "https://docs.example.com/reference/authentication/",
    ]


@pytest.mark.asyncio
async def test_offline_mkdocs_index_avoids_network(monkeypatch: pytest.MonkeyPatch):
    site_search._sitemap_cache.clear()
    site_search._sitemap_locks.clear()
    site_search._index_cache.clear()
    site_search._index_locks.clear()

    site_url = "https://docs.example.com/reference/"
    index_url = "https://docs.example.com/reference/search/search_index.json"
    site_search._index_cache[index_url] = site_search._IndexCacheEntry(
        fetched_at=datetime.now(),
        kind="mkdocs",
        payload=(
            {
                "location": "authentication/middleware/",
                "title": "Authentication middleware",
                "text": "Authentication middleware reference and examples.",
            },
        ),
    )

    async def should_not_fetch(*args, **kwargs):
        raise AssertionError("Should not fetch MkDocs index in offline mode")

    monkeypatch.setattr(site_search, "_fetch_bytes", should_not_fetch)

    async with httpx.AsyncClient() as client:
        result = await site_search.search_site_via_sitemap(
            f"site:{site_url} authentication middleware",
            client,
            user_agent="tests",
            num_results=1,
            allow_network=False,
        )

    assert (
        result["organic"][0]["link"]
        == "https://docs.example.com/reference/authentication/middleware/"
    )
