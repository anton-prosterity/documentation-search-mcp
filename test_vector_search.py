"""Unit tests for vector search and reranking functionality."""

import pytest
import numpy as np
from pathlib import Path
import tempfile

from src.documentation_search_enhanced.vector_search import (
    VectorSearchEngine,
    SearchResult,
    get_vector_engine,
)
from src.documentation_search_enhanced.reranker import SearchReranker, get_reranker
from src.documentation_search_enhanced.smart_search import (
    SearchResult as SmartSearchResult,
)


class TestVectorSearchEngine:
    """Test cases for VectorSearchEngine."""

    def test_initialization(self):
        """Test vector search engine initialization."""
        engine = VectorSearchEngine()
        assert engine.model_name == "all-MiniLM-L6-v2"
        assert engine.dimension == 384
        assert len(engine) == 0

    def test_embed_documents(self):
        """Test document embedding generation."""
        engine = VectorSearchEngine()
        documents = [
            "FastAPI is a modern web framework",
            "React is a JavaScript library",
            "Python is a programming language",
        ]

        embeddings = engine.embed_documents(documents)

        assert embeddings.shape == (3, 384)
        assert embeddings.dtype == np.float32

    def test_add_documents(self):
        """Test adding documents to the index."""
        engine = VectorSearchEngine()
        documents = [
            "How to use FastAPI authentication",
            "FastAPI security tutorial",
            "JWT authentication in FastAPI",
        ]

        index_ids = engine.add_documents(documents)

        assert len(index_ids) == 3
        assert len(engine) == 3
        assert engine.doc_store[0]["content"] == documents[0]

    def test_add_documents_with_metadata(self):
        """Test adding documents with custom metadata."""
        engine = VectorSearchEngine()
        documents = ["FastAPI docs", "React docs"]
        metadata = [{"source": "fastapi.com"}, {"source": "react.dev"}]
        doc_ids = ["doc1", "doc2"]

        engine.add_documents(documents, metadata=metadata, doc_ids=doc_ids)

        assert engine.doc_store[0]["doc_id"] == "doc1"
        assert engine.doc_store[0]["metadata"]["source"] == "fastapi.com"
        assert engine.doc_store[1]["doc_id"] == "doc2"

    def test_search_basic(self):
        """Test basic semantic search."""
        engine = VectorSearchEngine()
        documents = [
            "FastAPI is a web framework for building APIs with Python",
            "React is a JavaScript library for building user interfaces",
            "Django is a high-level Python web framework",
            "Vue.js is a progressive JavaScript framework",
        ]

        engine.add_documents(documents)

        # Search for Python web frameworks
        results = engine.search("Python web framework", top_k=2)

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].score > 0
        # Should find FastAPI and Django (both Python frameworks)
        assert "Python" in results[0].content
        assert "Python" in results[1].content

    def test_search_relevance_ordering(self):
        """Test that search results are ordered by relevance."""
        engine = VectorSearchEngine()
        documents = [
            "How to authenticate users in FastAPI",
            "FastAPI authentication and security guide",
            "React component lifecycle methods",
            "Python data structures tutorial",
        ]

        engine.add_documents(documents)

        results = engine.search("FastAPI authentication", top_k=4)

        # First two results should be about FastAPI authentication
        assert "FastAPI" in results[0].content
        assert "authentication" in results[0].content.lower()
        assert results[0].score > results[2].score

    def test_search_score_threshold(self):
        """Test search with score threshold."""
        engine = VectorSearchEngine()
        documents = [
            "FastAPI security best practices",
            "Unrelated document about cooking recipes",
        ]

        engine.add_documents(documents)

        results = engine.search("FastAPI security", top_k=10, score_threshold=0.5)

        # Should filter out low-relevance results
        for result in results:
            assert result.score >= 0.5

    def test_search_empty_index(self):
        """Test search on empty index."""
        engine = VectorSearchEngine()
        results = engine.search("test query")

        assert len(results) == 0

    def test_save_and_load_index(self):
        """Test saving and loading index from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test_index.faiss"

            # Create and populate engine
            engine1 = VectorSearchEngine(index_path=index_path)
            documents = [
                "FastAPI documentation",
                "React documentation",
                "Python tutorial",
            ]
            engine1.add_documents(documents)
            engine1.save_index()

            # Load in new engine
            engine2 = VectorSearchEngine(index_path=index_path)

            assert len(engine2) == 3
            assert engine2.doc_store[0]["content"] == documents[0]

    def test_clear_index(self):
        """Test clearing the index."""
        engine = VectorSearchEngine()
        engine.add_documents(["doc1", "doc2", "doc3"])

        assert len(engine) == 3

        engine.clear()

        assert len(engine) == 0
        assert len(engine.doc_store) == 0

    def test_global_instance(self):
        """Test global engine instance getter."""
        engine1 = get_vector_engine()
        engine2 = get_vector_engine()

        assert engine1 is engine2  # Same instance


class TestSearchReranker:
    """Test cases for SearchReranker."""

    def _create_search_result(
        self,
        doc_id: str,
        title: str,
        snippet: str,
        score: float = 0.5,
        url: str = "https://example.com",
    ) -> SmartSearchResult:
        """Helper to create SmartSearchResult objects."""
        return SmartSearchResult(
            source_library="fastapi",
            url=url,
            title=title,
            snippet=snippet,
            relevance_score=score,
            content_type="tutorial",
            difficulty_level="intermediate",
            code_snippets_count=1,
            estimated_read_time=5,
        )

    @pytest.mark.asyncio
    async def test_reranker_initialization(self):
        """Test reranker initialization with default weights."""
        reranker = SearchReranker()

        assert reranker.semantic_weight == 0.5
        assert reranker.keyword_weight == 0.3
        assert reranker.metadata_weight == 0.2

    @pytest.mark.asyncio
    async def test_reranker_weight_normalization(self):
        """Test that weights are normalized to sum to 1.0."""
        reranker = SearchReranker(
            semantic_weight=2.0, keyword_weight=1.0, metadata_weight=1.0
        )

        total = (
            reranker.semantic_weight
            + reranker.keyword_weight
            + reranker.metadata_weight
        )
        assert abs(total - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_rerank_basic(self):
        """Test basic reranking functionality."""
        reranker = SearchReranker()

        results = [
            self._create_search_result(
                "1", "FastAPI Tutorial", "Learn FastAPI basics", 0.5
            ),
            self._create_search_result(
                "2", "FastAPI Security", "Authentication in FastAPI", 0.6
            ),
            self._create_search_result(
                "3", "Random Doc", "Unrelated content", 0.4
            ),
        ]

        reranked = await reranker.rerank(results, "FastAPI authentication")

        # Results should be reordered
        assert len(reranked) == 3
        assert all(isinstance(r, SmartSearchResult) for r in reranked)

    @pytest.mark.asyncio
    async def test_rerank_semantic_disabled(self):
        """Test reranking with semantic search disabled."""
        reranker = SearchReranker()

        results = [
            self._create_search_result("1", "Doc 1", "Content 1", 0.8),
            self._create_search_result("2", "Doc 2", "Content 2", 0.5),
        ]

        reranked = await reranker.rerank(results, "test query", use_semantic=False)

        # Should still return results, just without semantic scoring
        assert len(reranked) == 2
        # Higher original score should still rank higher
        assert reranked[0].relevance_score > reranked[1].relevance_score

    @pytest.mark.asyncio
    async def test_rerank_empty_results(self):
        """Test reranking with empty results list."""
        reranker = SearchReranker()
        reranked = await reranker.rerank([], "test query")

        assert len(reranked) == 0

    @pytest.mark.asyncio
    async def test_metadata_scoring_official_docs(self):
        """Test that official documentation gets higher metadata scores."""
        reranker = SearchReranker()

        # Official docs should score higher
        official_result = self._create_search_result(
            "1",
            "Official Docs",
            "Content",
            0.5,
            url="https://fastapi.tiangolo.com/tutorial",
        )

        # Community content should score lower
        community_result = self._create_search_result(
            "2",
            "Blog Post",
            "Content",
            0.5,
            url="https://medium.com/some-article",
        )

        results = [community_result, official_result]
        reranked = await reranker.rerank(results, "FastAPI tutorial", use_semantic=False)

        # Official docs should rank higher due to metadata scoring
        assert reranked[0].url == official_result.url

    @pytest.mark.asyncio
    async def test_metadata_scoring_code_examples(self):
        """Test that results with code examples get boosted."""
        reranker = SearchReranker()

        result_with_code = SmartSearchResult(
            source_library="fastapi",
            url="https://example.com/1",
            title="Tutorial with Code",
            snippet="Example code",
            relevance_score=0.5,
            content_type="tutorial",
            difficulty_level="intermediate",
            code_snippets_count=5,  # Has code examples
            estimated_read_time=10,
        )

        result_without_code = SmartSearchResult(
            source_library="fastapi",
            url="https://example.com/2",
            title="Theory Only",
            snippet="No code",
            relevance_score=0.5,
            content_type="reference",
            difficulty_level="intermediate",
            code_snippets_count=0,  # No code examples
            estimated_read_time=10,
        )

        results = [result_without_code, result_with_code]
        reranked = await reranker.rerank(results, "code examples", use_semantic=False)

        # Result with code should rank higher
        assert reranked[0].code_snippets_count > 0

    @pytest.mark.asyncio
    async def test_global_reranker_instance(self):
        """Test global reranker instance getter."""
        reranker1 = get_reranker()
        reranker2 = get_reranker()

        assert reranker1 is reranker2  # Same instance


class TestIntegration:
    """Integration tests for vector search + reranking."""

    @pytest.mark.asyncio
    async def test_end_to_end_search_pipeline(self):
        """Test complete search pipeline with vector search and reranking."""
        # Setup
        engine = VectorSearchEngine()
        reranker = SearchReranker()

        # Index documents
        documents = [
            "FastAPI is a modern, fast web framework for building APIs with Python",
            "Learn how to implement JWT authentication in FastAPI applications",
            "FastAPI security best practices and common vulnerabilities",
            "React hooks tutorial for beginners",
        ]

        engine.add_documents(documents)

        # Perform vector search
        vector_results = engine.search("FastAPI security authentication", top_k=4)

        # Convert to SmartSearchResult format for reranking
        smart_results = []
        for i, result in enumerate(vector_results):
            smart_results.append(
                SmartSearchResult(
                    source_library="fastapi",
                    url=f"https://example.com/{i}",
                    title=f"Document {i}",
                    snippet=result.content,
                    relevance_score=result.score,
                    content_type="tutorial",
                    difficulty_level="intermediate",
                    code_snippets_count=1,
                    estimated_read_time=5,
                )
            )

        # Rerank results
        reranked = await reranker.rerank(
            smart_results, "FastAPI security authentication"
        )

        # Verify results
        assert len(reranked) > 0
        # Top results should be about FastAPI security/authentication
        top_result_text = reranked[0].snippet.lower()
        assert "fastapi" in top_result_text
        assert any(
            word in top_result_text for word in ["security", "authentication", "jwt"]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
