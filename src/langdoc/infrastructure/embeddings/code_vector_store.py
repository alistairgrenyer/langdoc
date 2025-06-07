"""Vector store implementation for code embeddings."""

import os
from pathlib import Path
from typing import Dict, List, Optional

import rich.console
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from langdoc.domain.interfaces import VectorStore
from langdoc.infrastructure.embeddings.document_processor import DocumentProcessor


class CodeVectorStore(VectorStore):
    """Vector store for code embeddings and similarity search."""

    def __init__(
        self,
        persist_directory: str = ".langdoc/vector_store",
        embedding_model: str = "all-MiniLM-L6-v2",
        console: Optional[rich.console.Console] = None,
    ):
        """Initialize the code vector store.
        
        Args:
            persist_directory: Directory to persist vector store
            embedding_model: HuggingFace embedding model to use
            console: Optional Rich console for output
        """
        self.console = console or rich.console.Console()
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.document_processor = DocumentProcessor(console=self.console)
        
        # Initialize embedding function
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        
        # Initialize vector store if directory exists
        if os.path.exists(persist_directory):
            self.db = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings,
            )
            self.console.print(
                f"[green]Loaded existing vector store from {persist_directory}[/green]",
            )
        else:
            self.db = None
            self.console.print(
                f"[yellow]No existing vector store found at {persist_directory}[/yellow]",
                # Line broken to fix line length
            )

    def index_codebase(
        self, 
        codebase_path: Path, 
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """Index a codebase into the vector store.
        
        Args:
            codebase_path: Path to the codebase root directory
            exclude_patterns: Optional list of glob patterns to exclude
            
        Returns:
            Dictionary with statistics about indexing
        """
        # Get documents from Git repository
        documents, processed_count, skipped_count = (
            self.document_processor.get_git_documents(
                codebase_path,
            )
        )
        
        # Apply exclude patterns if provided
        if exclude_patterns and documents:
            original_count = len(documents)
            documents = self._filter_documents(documents, exclude_patterns)
            filtered_count = original_count - len(documents)
            skipped_count += filtered_count
            self.console.print(
                f"Excluded {filtered_count} files based on exclude patterns",
            )
            
        # Create vector store directory if needed
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Create or update vector store
        if documents:
            self.db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
            )
            self.console.print(
                f"[green]Successfully indexed {len(documents)} documents[/green]",
            )
        else:
            self.console.print(
                "[yellow]No documents to index after filtering[/yellow]",
            )
            
        # Return statistics
        return {
            "processed": processed_count,
            "indexed": len(documents),
            "skipped": skipped_count,
        }

    def retrieve_relevant_context(
        self, 
        query: str, 
        max_documents: int = 5,
    ) -> List[Dict[str, str]]:
        """Retrieve relevant context based on a query.
        
        Args:
            query: Query string to search for
            max_documents: Maximum number of documents to retrieve
            
        Returns:
            List of relevant document dictionaries
        """
        if not self.db:
            self.console.print(
                "[yellow]Vector store not initialized. "
                "Please index codebase first.[/yellow]",
            )
            return []
            
        # Perform similarity search
        docs = self.db.similarity_search(query, k=max_documents)
        
        # Format results
        results = []
        for doc in docs:
            results.append({
                "source": doc.metadata.get("source", "unknown"),
                "content": doc.page_content,
                "type": doc.metadata.get("type", "unknown"),
            })
            
        return results

    def _filter_documents(
        self, 
        documents: List[Document], 
        exclude_patterns: List[str],
    ) -> List[Document]:
        """Filter documents based on exclude patterns.
        
        Args:
            documents: List of documents to filter
            exclude_patterns: List of glob patterns to exclude
            
        Returns:
            Filtered list of documents
        """
        import fnmatch
        
        filtered_docs = []
        for doc in documents:
            source = doc.metadata.get("source", "")
            exclude = False
            
            # Check if document matches any exclude pattern
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(source, pattern):
                    exclude = True
                    break
                    
            if not exclude:
                filtered_docs.append(doc)
                
        return filtered_docs
