"""Integration and E2E tests for vector search feature."""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from src.documentation_search_enhanced.vector_search import (
    VectorSearchEngine,
    get_vector_engine,
)
from src.documentation_search_enhanced.reranker import SearchReranker, get_reranker
from src.documentation_search_enhanced.smart_search import (
    SearchResult as SmartSearchResult,
)


class TestVectorSearchIntegration:
    """Integration tests for vector search with real components."""

    @pytest.mark.asyncio
    async def test_semantic_search_with_vector_rerank(self):
        """Test semantic_search tool with vector reranking enabled."""
        from src.documentation_search_enhanced.main import semantic_search

        # Mock the smart_search.semantic_search to return controlled results
        mock_results = [
            SmartSearchResult(
                source_library="fastapi",
                url="https://fastapi.tiangolo.com/tutorial/security/",
                title="FastAPI Security Tutorial",
                snippet="Learn how to implement authentication and authorization in FastAPI applications using OAuth2, JWT tokens, and security best practices.",
                relevance_score=0.7,
                content_type="tutorial",
                difficulty_level="intermediate",
                code_snippets_count=5,
                estimated_read_time=10,
            ),
            SmartSearchResult(
                source_library="fastapi",
                url="https://fastapi.tiangolo.com/advanced/security/",
                title="Advanced FastAPI Security",
                snippet="Advanced security patterns including OAuth2 with Password and Bearer, security dependencies, and custom authentication schemes.",
                relevance_score=0.6,
                content_type="guide",
                difficulty_level="advanced",
                code_snippets_count=3,
                estimated_read_time=15,
            ),
            SmartSearchResult(
                source_library="fastapi",
                url="https://blog.example.com/fastapi-auth",
                title="Blog: FastAPI Auth",
                snippet="A blog post about implementing authentication in FastAPI applications.",
                relevance_score=0.5,
                content_type="tutorial",
                difficulty_level="beginner",
                code_snippets_count=2,
                estimated_read_time=5,
            ),
        ]

        with patch(
            "src.documentation_search_enhanced.main.smart_search.semantic_search",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = mock_results

            # Test with vector reranking enabled (default)
            result = await semantic_search(
                query="FastAPI authentication security",
                libraries=["fastapi"],
                use_vector_rerank=True,
            )

            assert result["query"] == "FastAPI authentication security"
            assert result["libraries_searched"] == ["fastapi"]
            assert result["vector_rerank_enabled"] is True
            assert result["total_results"] == 3
            assert len(result["results"]) == 3

            # Results should be reranked - official docs should rank higher
            top_result = result["results"][0]
            assert "fastapi.tiangolo.com" in top_result["url"]
            assert top_result["relevance_score"] > 0

    @pytest.mark.asyncio
    async def test_semantic_search_without_vector_rerank(self):
        """Test semantic_search tool with vector reranking disabled."""
        from src.documentation_search_enhanced.main import semantic_search

        mock_results = [
            SmartSearchResult(
                source_library="react",
                url="https://react.dev/learn",
                title="React Documentation",
                snippet="Learn React with official documentation",
                relevance_score=0.8,
                content_type="tutorial",
                difficulty_level="beginner",
                code_snippets_count=1,
                estimated_read_time=5,
            ),
        ]

        with patch(
            "src.documentation_search_enhanced.main.smart_search.semantic_search",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = mock_results

            result = await semantic_search(
                query="React hooks",
                libraries=["react"],
                use_vector_rerank=False,
            )

            assert result["vector_rerank_enabled"] is False
            assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_multiple_libraries_vector_search(self):
        """Test vector search across multiple libraries."""
        from src.documentation_search_enhanced.main import semantic_search

        fastapi_results = [
            SmartSearchResult(
                source_library="fastapi",
                url="https://fastapi.tiangolo.com/",
                title="FastAPI Main",
                snippet="FastAPI framework documentation",
                relevance_score=0.7,
                content_type="tutorial",
                difficulty_level="beginner",
                code_snippets_count=1,
                estimated_read_time=5,
            ),
        ]

        django_results = [
            SmartSearchResult(
                source_library="django",
                url="https://docs.djangoproject.com/",
                title="Django Docs",
                snippet="Django framework documentation",
                relevance_score=0.6,
                content_type="tutorial",
                difficulty_level="beginner",
                code_snippets_count=1,
                estimated_read_time=5,
            ),
        ]

        with patch(
            "src.documentation_search_enhanced.main.smart_search.semantic_search",
            new_callable=AsyncMock,
        ) as mock_search:
            # Return different results for different libraries
            mock_search.side_effect = [fastapi_results, django_results]

            result = await semantic_search(
                query="web framework",
                libraries=["fastapi", "django"],
                use_vector_rerank=True,
            )

            assert result["total_results"] == 2
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_reranking_improves_relevance(self):
        """Test that reranking actually improves result relevance ordering."""
        reranker = SearchReranker()

        # Create results where the most relevant one has lower initial score
        results = [
            SmartSearchResult(
                source_library="fastapi",
                url="https://example.com/blog",
                title="Random Blog Post",
                snippet="Some unrelated content about cooking",
                relevance_score=0.9,  # High initial score but irrelevant
                content_type="tutorial",
                difficulty_level="beginner",
                code_snippets_count=0,
                estimated_read_time=5,
            ),
            SmartSearchResult(
                source_library="fastapi",
                url="https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/",
                title="OAuth2 with Password (and hashing), Bearer with JWT tokens",
                snippet="Learn how to implement OAuth2 with Password flow, hash passwords, and use JWT tokens for authentication in FastAPI applications.",
                relevance_score=0.6,  # Lower initial score but highly relevant
                content_type="tutorial",
                difficulty_level="intermediate",
                code_snippets_count=10,
                estimated_read_time=20,
            ),
        ]

        reranked = await reranker.rerank(
            results, "FastAPI OAuth2 JWT authentication", use_semantic=True
        )

        # After reranking, the more relevant result should rank higher
        # Official docs with code examples about the exact topic should win
        assert "fastapi.tiangolo.com" in reranked[0].url
        assert reranked[0].code_snippets_count > 0


class TestVectorSearchE2E:
    """End-to-end tests simulating real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_e2e_authentication_search(self):
        """E2E: User searches for authentication documentation."""
        engine = VectorSearchEngine()

        # Simulate documentation corpus
        docs = [
            "FastAPI provides built-in support for OAuth2 authentication with JWT tokens. "
            "Use the OAuth2PasswordBearer dependency to secure your endpoints.",
            "Django authentication system provides user authentication out of the box. "
            "It handles user accounts, groups, permissions and cookie-based user sessions.",
            "React doesn't have built-in authentication. You typically use JWT tokens "
            "stored in localStorage and send them in Authorization headers.",
            "Python's hashlib module provides secure hash functions for password storage. "
            "Always use bcrypt or argon2 for password hashing.",
            "Express.js authentication can be implemented using Passport.js middleware. "
            "Supports various strategies including local, OAuth, and JWT.",
        ]

        engine.add_documents(docs)

        # User searches for OAuth2 JWT authentication
        results = engine.search("OAuth2 JWT token authentication", top_k=3)

        assert len(results) > 0
        # FastAPI doc should rank highest (most relevant)
        assert "FastAPI" in results[0].content
        assert "OAuth2" in results[0].content
        assert results[0].score > 0.5

    @pytest.mark.asyncio
    async def test_e2e_semantic_understanding(self):
        """E2E: Test semantic understanding of synonymous queries."""
        engine = VectorSearchEngine()

        docs = [
            "How to validate user credentials and manage login sessions",
            "Database query optimization techniques for better performance",
            "Implementing role-based access control in web applications",
        ]

        engine.add_documents(docs)

        # Search using different terminology (semantic similarity)
        query1 = "user authentication and authorization"
        query2 = "verify user identity and permissions"

        results1 = engine.search(query1, top_k=1)
        results2 = engine.search(query2, top_k=1)

        # Both queries should find the authentication/authorization doc
        assert "credentials" in results1[0].content or "access control" in results1[0].content
        assert "credentials" in results2[0].content or "access control" in results2[0].content

        # Scores should be reasonably close (semantic similarity)
        assert abs(results1[0].score - results2[0].score) < 0.3

    @pytest.mark.asyncio
    async def test_e2e_filtering_low_relevance(self):
        """E2E: Test that low-relevance results are filtered out."""
        engine = VectorSearchEngine()

        docs = [
            "FastAPI authentication with OAuth2 and JWT tokens",
            "React component lifecycle methods and hooks",
            "Python data structures: lists, tuples, and dictionaries",
            "Docker containerization best practices",
        ]

        engine.add_documents(docs)

        # Search for authentication with high score threshold
        results = engine.search(
            "web API authentication security",
            top_k=10,
            score_threshold=0.4,
        )

        # Should only return highly relevant results
        assert len(results) <= 2
        for result in results:
            assert result.score >= 0.4

    @pytest.mark.asyncio
    async def test_e2e_performance_benchmarks(self):
        """E2E: Test performance metrics for production readiness."""
        engine = VectorSearchEngine()

        # Create a realistic corpus
        docs = [
            f"Documentation example {i}: Various topics about web development, "
            f"authentication, databases, and API design patterns."
            for i in range(100)
        ]

        # Benchmark indexing
        start = time.time()
        engine.add_documents(docs)
        index_time = time.time() - start

        assert index_time < 30, f"Indexing took {index_time:.2f}s, expected <30s"

        # Benchmark search
        start = time.time()
        results = engine.search("authentication API design", top_k=10)
        search_time = time.time() - start

        assert search_time < 1, f"Search took {search_time:.2f}s, expected <1s"
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_e2e_empty_query_handling(self):
        """E2E: Test handling of edge cases like empty queries."""
        engine = VectorSearchEngine()

        docs = ["Sample documentation content"]
        engine.add_documents(docs)

        # Empty query should still work (return all docs by relevance)
        results = engine.search("", top_k=10)
        assert len(results) >= 0  # Should not crash

    @pytest.mark.asyncio
    async def test_e2e_special_characters(self):
        """E2E: Test handling of special characters in queries."""
        engine = VectorSearchEngine()

        docs = [
            "OAuth2.0 authentication with JWT tokens",
            "FastAPI @app.get() decorator usage",
            "SQL injection prevention with ? placeholders",
        ]

        engine.add_documents(docs)

        # Query with special characters
        results = engine.search("OAuth2.0 @decorator usage", top_k=3)

        assert len(results) > 0
        # Should handle special characters gracefully

    @pytest.mark.asyncio
    async def test_e2e_multi_language_support(self):
        """E2E: Test handling of different programming languages."""
        engine = VectorSearchEngine()

        docs = [
            "Python FastAPI async/await for asynchronous operations",
            "JavaScript async/await promises in Node.js",
            "Go goroutines and channels for concurrency",
            "Rust async programming with tokio runtime",
        ]

        engine.add_documents(docs)

        # Search for async patterns
        results = engine.search("asynchronous programming patterns", top_k=4)

        assert len(results) >= 2
        # Should find multiple language implementations


class TestVectorSearchRobustness:
    """Test robustness and error handling."""

    @pytest.mark.asyncio
    async def test_large_document_handling(self):
        """Test handling of very large documents."""
        engine = VectorSearchEngine()

        # Create a very long document
        large_doc = "FastAPI authentication " * 1000

        engine.add_documents([large_doc])
        results = engine.search("FastAPI auth", top_k=1)

        assert len(results) == 1
        assert results[0].score > 0

    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """Test thread-safety with concurrent searches."""
        engine = VectorSearchEngine()

        docs = [f"Document {i} about various topics" for i in range(50)]
        engine.add_documents(docs)

        # Run multiple searches concurrently
        async def search_task(query):
            return engine.search(query, top_k=5)

        queries = [f"topic {i}" for i in range(10)]
        results = await asyncio.gather(*[search_task(q) for q in queries])

        assert len(results) == 10
        for result_list in results:
            assert isinstance(result_list, list)

    @pytest.mark.asyncio
    async def test_global_instance_isolation(self):
        """Test that global instances are properly isolated."""
        engine1 = get_vector_engine()
        engine2 = get_vector_engine()

        # Should be same instance
        assert engine1 is engine2

        # Clear and verify isolation
        engine1.add_documents(["test doc"])
        assert len(engine2) == 1

        engine1.clear()
        assert len(engine2) == 0

    @pytest.mark.asyncio
    async def test_reranker_with_malformed_results(self):
        """Test reranker handling of edge cases."""
        reranker = SearchReranker()

        # Results with missing/unusual data
        results = [
            SmartSearchResult(
                source_library="unknown",
                url="",
                title="",
                snippet="",
                relevance_score=0.5,
                content_type="unknown",
                difficulty_level="unknown",
                code_snippets_count=0,
                estimated_read_time=0,
            ),
        ]

        # Should not crash
        reranked = await reranker.rerank(results, "test query")
        assert len(reranked) == 1


class TestVectorSearchComparison:
    """Comparison tests: with vs without vector search."""

    @pytest.mark.asyncio
    async def test_ranking_improvement_comparison(self):
        """Compare ranking quality with and without vector reranking."""
        from src.documentation_search_enhanced.main import semantic_search

        # Create results where keyword matching alone gives poor ordering
        mock_results = [
            SmartSearchResult(
                source_library="fastapi",
                url="https://example.com/spam",
                title="FastAPI FastAPI FastAPI",  # Keyword stuffing
                snippet="FastAPI FastAPI FastAPI keyword stuffing",
                relevance_score=0.95,  # Artificially high
                content_type="tutorial",
                difficulty_level="beginner",
                code_snippets_count=0,
                estimated_read_time=1,
            ),
            SmartSearchResult(
                source_library="fastapi",
                url="https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/",
                title="Security - OAuth2 with JWT",
                snippet="Comprehensive guide to implementing OAuth2 authentication with JWT tokens in FastAPI applications for secure API access.",
                relevance_score=0.6,  # Lower score but better content
                content_type="tutorial",
                difficulty_level="intermediate",
                code_snippets_count=8,
                estimated_read_time=15,
            ),
        ]

        with patch(
            "src.documentation_search_enhanced.main.smart_search.semantic_search",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = mock_results

            # Without vector reranking
            result_no_vector = await semantic_search(
                query="FastAPI OAuth2 authentication implementation",
                libraries=["fastapi"],
                use_vector_rerank=False,
            )

            # With vector reranking
            result_with_vector = await semantic_search(
                query="FastAPI OAuth2 authentication implementation",
                libraries=["fastapi"],
                use_vector_rerank=True,
            )

            # Without vector: spam doc ranks first (higher keyword score)
            assert result_no_vector["results"][0]["url"] == "https://example.com/spam"

            # With vector: quality doc should rank first (semantic understanding)
            assert "tiangolo.com" in result_with_vector["results"][0]["url"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
