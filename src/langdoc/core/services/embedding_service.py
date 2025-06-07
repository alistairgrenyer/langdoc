"""
Embedding service for managing code embeddings.
Provides centralized functionality for creating and managing vector embeddings.
"""
import os
import logging
from typing import List, Optional, Tuple

from langdoc.core.embedding import CodeEmbedder
from langdoc.cli.utils import get_parsed_files

logger = logging.getLogger("langdoc.embedding")

class EmbeddingService:
    """Service for managing code embeddings and vector stores."""
    
    def __init__(self, repo_path: str, file_ext: str = '.py', skip_dirs: Optional[List[str]] = None):
        """
        Initialize the embedding service.
        
        Args:
            repo_path: Path to the repository
            file_ext: File extension to filter (e.g., '.py')
            skip_dirs: List of directories to skip during parsing
        """
        self.repo_path = repo_path
        self.file_ext = file_ext
        self.skip_dirs = skip_dirs or []
        self.embedder = CodeEmbedder(repo_path=self.repo_path)
        self.logger = logger

    def embeddings_exist(self) -> bool:
        """
        Check if embeddings exist for the current repository.
        
        Returns:
            True if embeddings exist and can be loaded, False otherwise
        """
        # Check if Chroma database exists for this repository
        db_path = os.path.join(self.repo_path, self.embedder.DB_DIR)
        collection_name = self.embedder._collection_name
        collection_path = os.path.join(db_path, collection_name)
        
        return (os.path.exists(collection_path) and 
                os.path.exists(os.path.join(collection_path, "chroma.sqlite3")))
    
    def load_existing_embeddings(self) -> bool:
        """
        Load existing embeddings if they exist.
        
        Returns:
            True if embeddings were successfully loaded, False otherwise
        """
        if not self.embeddings_exist():
            self.logger.warning(f"No embeddings found at {self.repo_path}")
            return False
            
        try:
            if self.embedder.load_vector_store():
                self.logger.info("Successfully loaded existing embeddings")
                return True
            else:
                self.logger.warning("Failed to load existing embeddings")
                return False
        except Exception as e:
            self.logger.error(f"Error loading embeddings: {e}")
            return False
    
    def create_embeddings(self, force_rebuild: bool = False) -> Tuple[bool, Optional[CodeEmbedder]]:
        """
        Create or rebuild embeddings for the repository.
        
        Args:
            force_rebuild: If True, rebuild embeddings even if they exist
            
        Returns:
            Tuple of (success, embedder) where success is True if embeddings were created successfully
            and embedder is the CodeEmbedder object if successful, or None if failed
        """
        # Check for existing embeddings
        if self.embeddings_exist() and not force_rebuild:
            if self.load_existing_embeddings():
                self.logger.info("Using existing embeddings")
                return True, self.embedder
            else:
                self.logger.warning("Failed to load existing embeddings, will rebuild")
        elif force_rebuild and self.embeddings_exist():
            self.logger.info("Force rebuild requested, clearing existing embeddings")
            CodeEmbedder.clear_embeddings(self.repo_path)
            
        # Parse files and create embeddings
        return self._build_embeddings()
    
    def _build_embeddings(self) -> Tuple[bool, Optional[CodeEmbedder]]:
        """
        Internal method to build embeddings from parsed files.
        
        Returns:
            Tuple of (success, embedder)
        """
        try:
            # Parse files
            parsed_files = get_parsed_files(self.repo_path, self.file_ext, self.skip_dirs)
            if not parsed_files:
                self.logger.warning("No files parsed. Cannot create embeddings.")
                return False, None

            self.logger.info(f"Creating documents from {len(parsed_files)} parsed files...")
            documents_to_embed = self.embedder.create_documents_from_parsed_data(parsed_files)

            if not documents_to_embed:
                self.logger.warning("No documents created for embedding")
                return False, None

            self.logger.info(f"Building vector store with {len(documents_to_embed)} documents...")
            if self.embedder.build_vector_store(documents_to_embed):
                self.logger.info("Vector store built successfully")
                # Save metadata explicitly
                self.embedder.save_vector_store()
                return True, self.embedder
            else:
                self.logger.error("Failed to build vector store")
                return False, None
                
        except Exception as e:
            self.logger.exception(f"Error building embeddings: {e}")
            return False, None
    
    def get_or_create_embeddings(self, force_rebuild: bool = False) -> Optional[CodeEmbedder]:
        """
        Get existing embeddings or create new ones if they don't exist.
        
        Args:
            force_rebuild: If True, rebuild embeddings even if they exist
            
        Returns:
            CodeEmbedder instance with loaded vector store, or None if failed
        """
        if not force_rebuild and self.embeddings_exist():
            if self.load_existing_embeddings():
                return self.embedder
        
        # No embeddings or forced rebuild - create new ones
        success, embedder = self.create_embeddings(force_rebuild=force_rebuild)
        if success:
            return embedder
        else:
            return None
