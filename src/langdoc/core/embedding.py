# embedding.py
"""
Embedding module for creating and managing code embeddings with persistent storage.

This module handles:
1. Creating embeddings from parsed code
2. Storing embeddings in SQLite with LangChain's Chroma
3. Tracking repository metadata to ensure embedding relevance
4. Providing retrieval capabilities for RAG-based functionality
"""

import os
import json
import hashlib
import platform
# SQLite is used internally by Chroma
from datetime import datetime
from typing import List, Dict, Any
import shutil
import subprocess

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found. Please set it in your .env file or environment variables.")


def get_repo_metadata(repo_path: str) -> Dict[str, str]:
    """Get metadata about the git repository for tracking changes.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Dict with repo_path, branch, commit_hash, and repo_id (unique identifier)
    """
    # Get absolute path to normalize across systems
    abs_path = os.path.abspath(repo_path)
    
    # Initialize with default values
    metadata = {
        "repo_path": abs_path,
        "branch": "unknown",
        "commit_hash": "unknown"
    }
    
    try:
        # Get current branch
        branch_cmd = subprocess.run(
            ["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=False
        )
        if branch_cmd.returncode == 0:
            metadata["branch"] = branch_cmd.stdout.strip()
            
        # Get current commit hash
        hash_cmd = subprocess.run(
            ["git", "-C", repo_path, "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False
        )
        if hash_cmd.returncode == 0:
            metadata["commit_hash"] = hash_cmd.stdout.strip()
            
        # Try to get remote origin URL for better identification
        try:
            origin_cmd = subprocess.run(
                ["git", "-C", repo_path, "config", "--get", "remote.origin.url"],
                capture_output=True, text=True, check=False
            )
            if origin_cmd.returncode == 0 and origin_cmd.stdout.strip():
                metadata["remote_url"] = origin_cmd.stdout.strip()
        except Exception:
            pass  # Not critical, continue without remote URL
            
    except Exception as e:
        print(f"Warning: Could not retrieve git metadata: {e}")
    
    # Generate a repo_id that includes the commit hash if available
    # This ensures embeddings are regenerated when the repository changes
    id_components = abs_path
    if metadata["commit_hash"] != "unknown":
        id_components += metadata["commit_hash"]
    
    metadata["repo_id"] = hashlib.md5(id_components.encode()).hexdigest()
        
    return metadata

class CodeEmbedder:
    """
    Manages code embeddings with persistent SQLite storage through LangChain's Chroma.
    
    This class handles:
    - Creating embeddings from parsed code files
    - Storing embeddings in SQLite with metadata
    - Loading embeddings based on repository identity
    - Providing similarity search for RAG
    """
    # Storage configuration - follow platform conventions for cache directories
    @staticmethod
    def _get_cache_dir():
        """Get the appropriate cache directory based on the platform."""
        if platform.system() == "Windows":
            # On Windows, use %LOCALAPPDATA%\langdoc\cache\embeddings
            base_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            return os.path.join(base_dir, "langdoc", "cache", "embeddings")
        else:
            # On Linux/macOS, use ~/.cache/langdoc/embeddings
            return os.path.join(os.path.expanduser("~"), ".cache", "langdoc", "embeddings")
    
    DB_DIR = _get_cache_dir()  # Get the cache directory at module load time
    COLLECTION_PREFIX = "langdoc_"  # Prefix for Chroma collections
    
    def __init__(self, model_name: str = "text-embedding-ada-002", chunk_size: int = 1000, 
                 chunk_overlap: int = 100, repo_path: str = "."):
        """Initialize the embedding system for the given repository.
        
        Args:
            model_name: OpenAI embedding model to use
            chunk_size: Size of text chunks for embeddings
            chunk_overlap: Overlap between chunks
            repo_path: Path to the repository to work with
        """
        # Ensure we have the API key
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found. Please set it in your environment variables or .env file.")
            
        # Initialize embeddings model
        self.embeddings_model = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Set up database path and collection name
        self.repo_path = os.path.abspath(repo_path)
        self.metadata = get_repo_metadata(self.repo_path)
        
        # Make sure the database directory exists
        os.makedirs(self.DB_DIR, exist_ok=True)
        
        # Use global storage location in user's home directory
        self.db_path = self.DB_DIR
        self._collection_name = self._get_collection_name()
        
        # Initialize vector store (to be built or loaded)
        self.vector_store = None

    def _get_collection_name(self) -> str:
        """Generate a unique collection name based on repository ID."""
        return f"{self.COLLECTION_PREFIX}{self.metadata['repo_id']}"
        
    def create_documents_from_parsed_data(self, parsed_files: List[Dict[str, Any]]) -> List[Document]:
        """Creates LangChain Document objects from parsed file data.
        
        Args:
            parsed_files: List of parsed file data dictionaries
            
        Returns:
            List of LangChain Document objects ready for embedding
        """
        documents = []
        
        for file_data in parsed_files:
            file_path = file_data["file_path"]
            content = file_data["content"]
            rel_path = os.path.relpath(file_path, self.repo_path)
            
            # Add file-level embedding with whole file content for context
            file_metadata = {
                "source": rel_path,
                "file_path": rel_path,
                "type": "file",
                "language": os.path.splitext(file_path)[1].replace(".", ""),
                "repo_id": self.metadata["repo_id"]
            }
            
            # Create chunks for the file content to keep within token limits
            file_chunks = self.text_splitter.create_documents(
                texts=[content],
                metadatas=[file_metadata]
            )
            documents.extend(file_chunks)
            
            # Add more specific embeddings for functions and classes if available
            for definition in file_data.get("definitions", []):
                definition_code = definition.get("code", "")
                if not definition_code:
                    continue
                    
                def_metadata = {
                    "source": f"{rel_path}:{definition['name']}",
                    "file_path": rel_path,
                    "type": definition["type"],
                    "name": definition["name"],
                    "lineno": definition.get("lineno", 0),
                    "language": os.path.splitext(file_path)[1].replace(".", ""),
                    "repo_id": self.metadata["repo_id"]
                }
                
                # Split large definitions into chunks
                def_chunks = self.text_splitter.create_documents(
                    texts=[definition_code],
                    metadatas=[def_metadata]
                )
                documents.extend(def_chunks)
                
        return documents
        
    def build_vector_store(self, documents: List[Document]) -> bool:
        """Builds or updates the Chroma vector store with the given documents.
        
        Args:
            documents: List of LangChain Document objects to embed
            
        Returns:
            True if successful, False otherwise
        """
        if not documents:
            print("No documents to embed. Vector store not built.")
            return False
            
        print(f"Building vector store with {len(documents)} documents...")
        
        try:
            # Create a new Chroma instance with our documents
            persist_directory = os.path.join(self.db_path, self._collection_name)
            
            # Ensure the directory exists
            os.makedirs(persist_directory, exist_ok=True)
            
            # Create new vector store
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings_model,
                persist_directory=persist_directory,
                collection_name=self._collection_name
            )
            
            # Persist to disk
            self.vector_store.persist()
            
            # Save metadata for tracking changes
            metadata_path = os.path.join(persist_directory, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump({
                    "repo_metadata": self.metadata,
                    "collection_name": self._collection_name,
                    "embedding_model": self.embeddings_model.model,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "document_count": len(documents)
                }, f, indent=2)
            
            print(f"Vector store built and saved to {persist_directory}")
            return True
        except Exception as e:
            print(f"Error building vector store: {e}")
            return False
            
    def load_vector_store(self, force: bool = False) -> bool:
        """Loads the Chroma vector store from disk for the current repository.
        
        Args:
            force: If True, load even if repository metadata doesn't match
            
        Returns:
            True if vector store was successfully loaded, False otherwise
        """
        try:
            persist_directory = os.path.join(self.db_path, self._collection_name)
            
            # Check if the collection directory exists
            if not os.path.exists(persist_directory):
                print(f"No vector store found at {persist_directory}")
                return False
                
            # Load existing index
            self.vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings_model,
                collection_name=self._collection_name
            )
            
            # Verify repository metadata unless force is True
            if not force:
                # Try to load metadata file
                try:
                    metadata_path = os.path.join(persist_directory, "metadata.json")
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            stored_metadata = json.load(f)
                            
                        # Check if this is the same repository commit
                        stored_repo_meta = stored_metadata.get("repo_metadata", {})
                        stored_commit = stored_repo_meta.get("commit_hash")
                        current_commit = self.metadata.get("commit_hash")
                        
                        if stored_commit and current_commit and stored_commit != current_commit:
                            print("Warning: Repository has changed since embeddings were created.")
                            print(f"Stored commit: {stored_commit}")
                            print(f"Current commit: {current_commit}")
                            print("Consider rebuilding the vector store for accuracy.")
                            # Just warn but continue loading
                        
                        # Verify repo path as additional check
                        saved_repo_path = stored_repo_meta.get("repo_path")
                        if saved_repo_path and saved_repo_path != self.repo_path:
                            print("Warning: Vector store was created in a different location.")
                            print(f"Current path: {self.repo_path}")
                            print(f"Stored path: {saved_repo_path}")
                            # Just warn but continue loading
                    
                except Exception as e:
                    print(f"Warning: Could not verify repository metadata: {e}")
            
            print(f"Vector store loaded from {persist_directory}")
            return True
        except Exception as e:
            print(f"Error loading Chroma vector store: {e}")
            self.vector_store = None
            return False

    def save_vector_store(self) -> bool:
        """Persists the Chroma vector store to disk.
        
        Note that Chroma automatically handles persistence,
        this method is mainly for explicit saves and compatibility.
        
        Returns:
            True if successful, False otherwise
        """
        if self.vector_store is None:
            print("No vector store to save.")
            return False
        
        try:
            # For Chroma, we just need to call persist()
            self.vector_store.persist()
            print(f"Vector store explicitly persisted to {self.db_path}")
            
            # Save metadata for easier inspection
            metadata_path = os.path.join(self.db_path, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump({
                    "repo_metadata": self.metadata,
                    "collection_name": self._collection_name,
                    "embedding_model": self.embeddings_model.model,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                }, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error persisting Chroma vector store: {e}")
            return False
            
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Performs similarity search on the vector store.
        
        Args:
            query: The query text to search for
            k: Number of results to return
            
        Returns:
            List of Document objects matching the query
        """
        if not self.vector_store:
            print("Vector store not initialized. Cannot perform similarity search.")
            return []
            
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []
            
    @classmethod
    def clear_embeddings(cls, repo_path: str) -> bool:
        """Clears all embeddings for the specified repository.
        
        Args:
            repo_path: Path to the repository to clear embeddings for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get repo metadata to determine collection name
            metadata = get_repo_metadata(repo_path)
            repo_id = metadata.get("repo_id")
            
            # Build the path to the database directory - now using global location
            db_path = cls.DB_DIR
            collection_dir = os.path.join(db_path, f"{cls.COLLECTION_PREFIX}{repo_id}")
            
            if os.path.exists(collection_dir):
                print(f"Removing embeddings at {collection_dir}")
                shutil.rmtree(collection_dir, ignore_errors=True)
                print("Embeddings cleared successfully.")
                return True
            else:
                print(f"No embeddings found for repository at {collection_dir}")
                return False
        except Exception as e:
            print(f"Error clearing embeddings: {e}")
            return False
