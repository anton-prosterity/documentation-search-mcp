"""Vector search engine for semantic documentation search using sentence transformers and FAISS."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)

# Try to import vector search dependencies (optional)
try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer

    VECTOR_SEARCH_AVAILABLE = True
except ImportError as e:
    VECTOR_SEARCH_AVAILABLE = False
    logger.warning(
        f"Vector search dependencies not available: {e}. "
        "Install with: pip install documentation-search-enhanced[vector]"
    )


class SearchResult:
    """Container for search results with score and metadata."""

    def __init__(
        self,
        doc_id: str,
        content: str,
        score: float,
        metadata: Optional[Dict] = None,
    ):
        self.doc_id = doc_id
        self.content = content
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
        }


class VectorSearchEngine:
    """
    Semantic search engine using sentence transformers for embeddings and FAISS for vector similarity.

    Uses the all-MiniLM-L6-v2 model which provides:
    - 384-dimensional embeddings
    - Good balance between speed and quality
    - ~120MB model size
    - Optimized for semantic search
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_path: Optional[Path] = None,
    ):
        """
        Initialize the vector search engine.

        Args:
            model_name: Name of the sentence-transformers model to use
            index_path: Optional path to save/load FAISS index
        """
        if not VECTOR_SEARCH_AVAILABLE:
            raise ImportError(
                "Vector search dependencies not installed. "
                "Install with: pip install documentation-search-enhanced[vector]"
            )

        self.model_name = model_name
        self.index_path = index_path
        self.dimension = 384  # all-MiniLM-L6-v2 embedding dimension

        logger.info(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Initialize FAISS index (L2 distance for cosine similarity)
        self.index = faiss.IndexFlatL2(self.dimension)

        # Document store: maps index position to document data
        self.doc_store: Dict[int, Dict] = {}
        self.next_id = 0

        # Load existing index if path provided
        if index_path and index_path.exists():
            self.load_index(index_path)

    def embed_documents(self, documents: List[str]) -> "np.ndarray":
        """
        Generate embeddings for a list of documents.

        Args:
            documents: List of text documents to embed

        Returns:
            numpy array of shape (n_documents, embedding_dimension)
        """
        logger.debug(f"Embedding {len(documents)} documents")
        embeddings = self.model.encode(
            documents,
            convert_to_numpy=True,
            show_progress_bar=len(documents) > 100,
        )
        return embeddings

    def add_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict]] = None,
        doc_ids: Optional[List[str]] = None,
    ) -> List[int]:
        """
        Add documents to the vector index.

        Args:
            documents: List of text documents to index
            metadata: Optional list of metadata dicts for each document
            doc_ids: Optional list of custom document IDs

        Returns:
            List of internal index IDs for the added documents
        """
        if not documents:
            return []

        # Generate embeddings
        embeddings = self.embed_documents(documents)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Add to FAISS index
        start_id = self.next_id
        self.index.add(embeddings)

        # Store document data
        metadata = metadata or [{} for _ in documents]
        doc_ids = doc_ids or [f"doc_{start_id + i}" for i in range(len(documents))]

        index_ids = []
        for i, (doc, meta, doc_id) in enumerate(zip(documents, metadata, doc_ids)):
            internal_id = start_id + i
            self.doc_store[internal_id] = {
                "doc_id": doc_id,
                "content": doc,
                "metadata": meta,
            }
            index_ids.append(internal_id)

        self.next_id += len(documents)
        logger.info(
            f"Added {len(documents)} documents to index (total: {self.next_id})"
        )

        return index_ids

    def search(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Perform semantic search for similar documents.

        Args:
            query: Search query text
            top_k: Number of top results to return
            score_threshold: Optional minimum similarity score (0-1, higher is more similar)

        Returns:
            List of SearchResult objects sorted by relevance
        """
        if self.index.ntotal == 0:
            logger.warning("No documents in index")
            return []

        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)

        # Search FAISS index
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)

        # Convert to SearchResult objects
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue

            doc_data = self.doc_store.get(int(idx))
            if not doc_data:
                continue

            # Convert L2 distance to similarity score (0-1, higher is better)
            # For normalized vectors: L2 distance = sqrt(2 - 2*cosine_similarity)
            # So: similarity = 1 - (distance^2 / 2)
            similarity = 1 - (distance**2 / 2)

            # Apply score threshold if provided
            if score_threshold is not None and similarity < score_threshold:
                continue

            results.append(
                SearchResult(
                    doc_id=doc_data["doc_id"],
                    content=doc_data["content"],
                    score=float(similarity),
                    metadata=doc_data["metadata"],
                )
            )

        logger.debug(f"Found {len(results)} results for query: {query[:50]}...")
        return results

    def save_index(self, path: Optional[Path] = None):
        """
        Save FAISS index and document store to disk.

        Args:
            path: Path to save index (uses self.index_path if not provided)
        """
        save_path = path or self.index_path
        if not save_path:
            raise ValueError("No index path provided")

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(save_path))

        # Save document store
        import pickle

        doc_store_path = save_path.with_suffix(".docstore")
        with open(doc_store_path, "wb") as f:
            pickle.dump(
                {"doc_store": self.doc_store, "next_id": self.next_id},
                f,
            )

        logger.info(f"Saved index to {save_path}")

    def load_index(self, path: Path):
        """
        Load FAISS index and document store from disk.

        Args:
            path: Path to load index from
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Index not found at {path}")

        # Load FAISS index
        self.index = faiss.read_index(str(path))

        # Load document store
        import pickle

        doc_store_path = path.with_suffix(".docstore")
        with open(doc_store_path, "rb") as f:
            data = pickle.load(f)
            self.doc_store = data["doc_store"]
            self.next_id = data["next_id"]

        logger.info(f"Loaded index from {path} ({self.index.ntotal} documents)")

    def clear(self):
        """Clear all documents from the index."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.doc_store = {}
        self.next_id = 0
        logger.info("Cleared vector index")

    def __len__(self) -> int:
        """Return number of documents in index."""
        return self.index.ntotal


# Global instance for reuse
_vector_engine: Optional[VectorSearchEngine] = None


def get_vector_engine() -> VectorSearchEngine:
    """Get or create the global vector search engine instance."""
    global _vector_engine
    if _vector_engine is None:
        _vector_engine = VectorSearchEngine()
    return _vector_engine
