"""
Protocols defining interfaces for various components in the langdoc system.
"""
from typing import List, Protocol, runtime_checkable
from langchain.docstore.document import Document

@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol defining the interface for embedding operations."""
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        ...
        
@runtime_checkable
class VectorStoreProvider(Protocol):
    """Protocol defining the interface for vector store operations."""
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Perform similarity search on the vector store.
        
        Args:
            query: The query text to search for
            k: Number of results to return
            
        Returns:
            List of Document objects matching the query
        """
        ...
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            True if successful, False otherwise
        """
        ...
        
    def persist(self) -> bool:
        """Persist the vector store to disk.
        
        Returns:
            True if successful, False otherwise
        """
        ...
