import asyncio


from documentation_search_enhanced import main


def test_get_docs_returns_structured_summary(monkeypatch):
    orig_search_fn = main.search_web
    orig_docs_map = dict(main.docs_urls)
    orig_limit = getattr(main.smart_search, "_results_limit", 5)

    async def fake_search(query, num_results=5):
        assert "site:" in query
        return {
            "organic": [
                {
                    "link": "https://example.com/doc1",
                    "title": "Example Doc",
                    "snippet": "Example snippet covering authentication flows."
                }
            ]
        }

    async def fake_fetch(url):
        return (
            "Authentication guide for FastAPI applications. "
            "Demonstrates OAuth2 dependencies and token workflows."
        )

    monkeypatch.setattr(main, "search_web", fake_search)
    monkeypatch.setattr(main, "fetch_url", fake_fetch)

    main.smart_search.configure(main.docs_urls, main.search_web, results_limit=1)

    try:
        result = asyncio.run(main.get_docs("authentication", "fastapi"))
    finally:
        main.smart_search.configure(orig_docs_map, orig_search_fn, results_limit=orig_limit)

    assert isinstance(result, dict)
    assert result["libraries"]
    first_library = result["libraries"][0]
    assert first_library["library"] == "fastapi"
    assert first_library["results"][0]["summary"]
    assert "fastapi" in result["summary_markdown"].lower()


def test_semantic_search_uses_configured_search(monkeypatch):
    orig_search_fn = main.search_web
    orig_docs_map = dict(main.docs_urls)
    orig_limit = getattr(main.smart_search, "_results_limit", 5)

    async def fake_search(query, num_results=5):
        assert "site:" in query
        return {
            "organic": [
                {
                    "link": "https://fastapi.example/guide",
                    "title": "FastAPI Auth Guide",
                    "snippet": "Detailed walkthrough"
                }
            ]
        }

    main.smart_search.configure(main.docs_urls, fake_search, results_limit=1)

    try:
        payload = asyncio.run(main.semantic_search("authentication", "fastapi"))
    finally:
        main.smart_search.configure(orig_docs_map, orig_search_fn, results_limit=orig_limit)

    assert payload["total_results"] == 1
    assert payload["results"][0]["source_library"] == "fastapi"
    assert payload["results"][0]["url"] == "https://fastapi.example/guide"
