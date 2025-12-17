"""Search result reranking using hybrid scoring (vector + keyword + metadata)."""

import logging
import re
from typing import List, Optional

from .vector_search import get_vector_engine
from .smart_search import SearchResult

logger = logging.getLogger(__name__)


class SearchReranker:
    """
    Rerank search results using a hybrid scoring approach:
    - Semantic similarity (vector embeddings): 50% weight
    - Keyword matching relevance: 30% weight
    - Source authority/freshness: 20% weight
    """

    def __init__(
        self,
        semantic_weight: float = 0.5,
        keyword_weight: float = 0.3,
        metadata_weight: float = 0.2,
    ):
        """
        Initialize the reranker with configurable weights.

        Args:
            semantic_weight: Weight for vector similarity score (0-1)
            keyword_weight: Weight for keyword matching score (0-1)
            metadata_weight: Weight for metadata scoring (0-1)
        """
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.metadata_weight = metadata_weight

        # Ensure weights sum to 1.0
        total = semantic_weight + keyword_weight + metadata_weight
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Reranker weights sum to {total}, normalizing to 1.0")
            self.semantic_weight /= total
            self.keyword_weight /= total
            self.metadata_weight /= total

        self.vector_engine = get_vector_engine()

    async def rerank(
        self,
        results: List[SearchResult],
        query: str,
        use_semantic: bool = True,
    ) -> List[SearchResult]:
        """
        Rerank search results using hybrid scoring.

        Args:
            results: List of search results to rerank
            query: Original search query
            use_semantic: Whether to use semantic scoring (can be disabled for speed)

        Returns:
            Reranked list of search results
        """
        if not results:
            return results

        logger.debug(f"Reranking {len(results)} results for query: {query[:50]}...")

        # Calculate scores for each result
        scored_results = []
        for result in results:
            score = 0.0

            # 1. Semantic similarity score (if enabled)
            if use_semantic:
                semantic_score = await self._calculate_semantic_score(
                    query, result.snippet + " " + result.title
                )
                score += semantic_score * self.semantic_weight
            else:
                # If semantic disabled, redistribute weight to keyword matching
                score += result.relevance_score * (
                    self.semantic_weight + self.keyword_weight
                )

            # 2. Keyword matching score (use existing relevance_score)
            if not use_semantic:
                # Already included above
                pass
            else:
                score += result.relevance_score * self.keyword_weight

            # 3. Metadata scoring (authority, content quality indicators)
            metadata_score = self._calculate_metadata_score(result)
            score += metadata_score * self.metadata_weight

            # Store the hybrid score
            result.relevance_score = score
            scored_results.append(result)

        # Sort by hybrid score
        scored_results.sort(key=lambda r: r.relevance_score, reverse=True)

        logger.debug(
            f"Reranked results. Top score: {scored_results[0].relevance_score:.3f}"
        )
        return scored_results

    async def _calculate_semantic_score(self, query: str, document: str) -> float:
        """
        Calculate semantic similarity between query and document.

        Args:
            query: Search query
            document: Document text (title + snippet)

        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Generate embeddings
            query_embedding = self.vector_engine.embed_documents([query])
            doc_embedding = self.vector_engine.embed_documents([document])

            # Calculate cosine similarity
            import numpy as np

            query_norm = query_embedding / np.linalg.norm(query_embedding)
            doc_norm = doc_embedding / np.linalg.norm(doc_embedding)
            similarity = np.dot(query_norm[0], doc_norm[0])

            # Convert to 0-1 range (cosine similarity is -1 to 1)
            score = (similarity + 1) / 2
            return float(score)

        except Exception as e:
            logger.warning(f"Error calculating semantic score: {e}")
            return 0.5  # Neutral score on error

    def _calculate_metadata_score(self, result: SearchResult) -> float:
        """
        Calculate metadata-based score considering:
        - Source authority (official docs > blogs > forums)
        - Content type (tutorials/guides > reference > examples)
        - Code examples presence
        - Estimated quality indicators

        Args:
            result: Search result to score

        Returns:
            Metadata score between 0 and 1
        """
        score = 0.5  # Base score

        # Source authority scoring
        url_lower = result.url.lower()
        if any(
            domain in url_lower
            for domain in [
                "docs.python.org",
                "fastapi.tiangolo.com",
                "reactjs.org",
                "docs.djangoproject.com",
            ]
        ):
            score += 0.3  # Official documentation
        elif any(
            domain in url_lower
            for domain in ["github.com", "readthedocs.io", "readthedocs.org"]
        ):
            score += 0.2  # Authoritative sources
        elif any(
            domain in url_lower
            for domain in ["stackoverflow.com", "medium.com", "dev.to"]
        ):
            score += 0.1  # Community sources

        # Content type scoring
        content_type_scores = {
            "tutorial": 0.2,
            "guide": 0.2,
            "reference": 0.15,
            "example": 0.1,
        }
        score += content_type_scores.get(result.content_type.lower(), 0)

        # Code examples boost
        if result.code_snippets_count > 0:
            score += 0.1

        # URL structure quality (indicates well-organized docs)
        if self._has_good_url_structure(result.url):
            score += 0.05

        # Normalize to 0-1 range
        return min(1.0, max(0.0, score))

    def _has_good_url_structure(self, url: str) -> bool:
        """
        Check if URL has good structure (versioned, organized).

        Args:
            url: URL to check

        Returns:
            True if URL has good structure
        """
        # Check for version in URL
        has_version = bool(re.search(r"/v?\d+\.\d+/|/stable/|/latest/", url))

        # Check for organized path structure
        path_depth = len([p for p in url.split("/") if p]) - 2  # Exclude domain
        has_good_depth = 2 <= path_depth <= 6

        return has_version or has_good_depth


# Global instance
_reranker: Optional[SearchReranker] = None


def get_reranker() -> SearchReranker:
    """Get or create the global reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = SearchReranker()
    return _reranker
