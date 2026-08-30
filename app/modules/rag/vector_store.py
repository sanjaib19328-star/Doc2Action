import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.core.exceptions import BaseAppException


class VectorServiceException(BaseAppException):
    """Exception raised when vector database service operation fails or is unavailable."""

    def __init__(self, message: str = "Vector service operation failed", status_code: int = 503) -> None:
        super().__init__(message=message, status_code=status_code)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding generation."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass


class SimpleEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic pseudo-embedding provider for local/testing environments.
    Converts text characters to normalized float vectors.
    """

    def __init__(self, dimension: int = 128):
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        if not text:
            return vec

        text_lower = text.lower()
        for i, char in enumerate(text_lower):
            idx = (ord(char) * 31 + i) % self.dimension
            vec[idx] += 1.0

        # Normalize vector length
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class VectorDocument(ABC):
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None


class BaseVectorStore(ABC):
    """Abstract interface for Vector Store operations."""

    @abstractmethod
    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Upserts documents into the vector store."""
        pass

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Searches vector store by cosine similarity with metadata filtering."""
        pass

    @abstractmethod
    def delete_by_filter(self, filters: Dict[str, Any]) -> int:
        """Deletes vectors matching metadata filters."""
        pass


class InMemoryVectorStore(BaseVectorStore):
    """
    In-memory vector store implementation with cosine similarity search and metadata filtering.
    """

    def __init__(self):
        # Store dict: {doc_id: {"doc_id": ..., "content": ..., "metadata": ..., "vector": [...]}}
        self._store: Dict[str, Dict[str, Any]] = {}
        self.is_available: bool = True

    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        if not self.is_available:
            raise VectorServiceException("Vector store service is currently unavailable.")

        for doc in documents:
            doc_id = doc["doc_id"]
            self._store[doc_id] = doc

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return dot_product

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not self.is_available:
            raise VectorServiceException("Vector store service is currently unavailable.")

        results = []
        for doc_id, doc in self._store.items():
            metadata = doc.get("metadata", {})

            # Apply metadata filters
            match = True
            if filters:
                for k, v in filters.items():
                    if metadata.get(k) != v:
                        match = False
                        break
            if not match:
                continue

            sim = self._cosine_similarity(query_vector, doc.get("vector", []))
            results.append({
                "doc_id": doc_id,
                "score": sim,
                "content": doc.get("content"),
                "metadata": metadata,
            })

        # Sort by similarity score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_by_filter(self, filters: Dict[str, Any]) -> int:
        if not self.is_available:
            raise VectorServiceException("Vector store service is currently unavailable.")

        to_delete = []
        for doc_id, doc in self._store.items():
            metadata = doc.get("metadata", {})
            match = True
            for k, v in filters.items():
                if metadata.get(k) != v:
                    match = False
                    break
            if match:
                to_delete.append(doc_id)

        for doc_id in to_delete:
            del self._store[doc_id]

        return len(to_delete)


# Global singleton vector store instance for runtime/tests
vector_store_instance = InMemoryVectorStore()
embedding_provider_instance = SimpleEmbeddingProvider()
