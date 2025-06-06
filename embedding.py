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
    
    metadata = {
        "repo_path": abs_path,
        "branch": "unknown",
        "commit_hash": "unknown",
        "repo_id": hashlib.md5(abs_path.encode()).hexdigest()  # Unique ID for this repo
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
    # Storage configuration
    DB_DIR = ".langdoc_db"  # Directory for storing the SQLite database
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
        self.embeddings_model = OpenAIEmbeddings(model=model_name, openai_api_key=OPENAI_API_KEY)
        
        # Configure text splitter for code
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", "", "\nclass ", "\ndef "]
        )
        
        # Repository information
        self.repo_path = os.path.abspath(repo_path)
        self.metadata = get_repo_metadata(repo_path)
        
        # Generate a collection name based on repo metadata
        self._collection_name = self._get_collection_name()
        
        # Set up database directory
        self.db_path = os.path.join(self.repo_path, self.DB_DIR)
        os.makedirs(self.db_path, exist_ok=True)
        
        # Vector store - will be lazily initialized when needed
        self.vector_store = None
    
    def _get_collection_name(self) -> str:
        """Generate a unique collection name based on repository ID."""
        repo_id = self.metadata.get("repo_id", hashlib.md5(self.repo_path.encode()).hexdigest())
        return f"{self.COLLECTION_PREFIX}{repo_id}"

    def create_documents_from_parsed_data(self, parsed_files: List[Dict[str, Any]]) -> List[Document]:
        """Creates LangChain Document objects from parsed file data.
        
        Args:
            parsed_files: List of parsed file data dictionaries
            
        Returns:
            List of LangChain Document objects ready for embedding
        """
        documents = []
        for file_data in parsed_files:
            file_path = file_data.get('file_path', 'Unknown')
            # First, add file-level documentation if available
            file_docstring = file_data.get('file_docstring')
            if file_docstring:
                documents.append(Document(
                    page_content=file_docstring,
                    metadata={
                        "source": file_path,
                        "type": "file_docstring",
                        "name": os.path.basename(file_path),
                        "repo_path": self.repo_path,
                        "repo_id": self.metadata.get("repo_id"),
                        "branch": self.metadata.get("branch"),
                        "commit_hash": self.metadata.get("commit_hash"),
                    }
                ))
            
            # Add each definition with its docstring
            for definition in file_data.get('definitions', []):
                name = definition.get('name', 'Unknown')
                def_type = definition.get('type', 'Unknown')  # class, function, etc.
                docstring = definition.get('docstring', '')
                code = definition.get('code', '')
                signature = definition.get('signature', '')
                
                # Combine relevant information
                content = f"Name: {name}\nType: {def_type}\nSignature: {signature}\n"
                if docstring:
                    content += f"Docstring: {docstring}\n"
                if code:
                    content += f"Code:\n{code}"
                
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "source": file_path,
                        "type": def_type,
                        "name": name,
                        "definition": True,
                        "repo_path": self.repo_path,
                        "repo_id": self.metadata.get("repo_id"),
                        "branch": self.metadata.get("branch"),
                        "commit_hash": self.metadata.get("commit_hash"),
                    }
                ))
        
        # Apply text splitting to make chunks suitable for embedding
        if documents:
            return self.text_splitter.split_documents(documents)
        return []

    def build_vector_store(self, documents: List[Document]) -> bool:
        """Builds or updates the Chroma vector store with the given documents.
        
        Args:
            documents: List of LangChain Document objects to embed
            
        Returns:
            True if successful, False otherwise
        """
        if not documents:
            print("No documents to build vector store.")
            return False
        
        if not OPENAI_API_KEY:
            print("Cannot build vector store: OPENAI_API_KEY is not set.")
            return False
        
        try:
            # Create a Chroma vector store with SQLite persistence
            print(f"Building vector store with {len(documents)} documents...")
            persist_directory = os.path.join(self.db_path, self._collection_name)
            
            # Ensure directory exists
            os.makedirs(persist_directory, exist_ok=True)
            
            # Create or update the vector store
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings_model,
                persist_directory=persist_directory,
                collection_name=self._collection_name,
                collection_metadata={
                    "repo_id": self.metadata.get("repo_id"),
                    "repo_path": self.repo_path,
                    "branch": self.metadata.get("branch"),
                    "commit_hash": self.metadata.get("commit_hash"),
                    "created_at": datetime.utcnow().isoformat() + "Z"
                }
            )
            
            # Explicitly persist to disk
            self.vector_store.persist()
            print("Vector store built and persisted successfully.")
            return True
        except Exception as e:
            print(f"Error building Chroma vector store: {e}")
            self.vector_store = None
            return False

    def load_vector_store(self, force: bool = False) -> bool:
        """Loads the Chroma vector store from disk for the current repository.
        
        Args:
            force: If True, load even if repository metadata doesn't match
            
        Returns:
            True if vector store was successfully loaded, False otherwise
        """
        # Check for API key
        if not OPENAI_API_KEY:
            print("Cannot load vector store: OPENAI_API_KEY is not set for embeddings.")
            return False
            
        # Determine path to the database
        persist_directory = os.path.join(self.db_path, self._collection_name)
        
        # Check if database files exist
        if not os.path.exists(persist_directory) or not os.path.exists(os.path.join(persist_directory, "chroma.sqlite3")):
            print(f"No Chroma database found at {persist_directory}. Please run the 'parse' command first.")
            return False
        
        try:
            # Load the Chroma collection
            self.vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings_model,
                collection_name=self._collection_name
            )
            
            # Check collection metadata if not forcing load
            if not force:
                try:
                    # Get collection metadata
                    collection_metadata = self.vector_store._collection.get()
                    if not collection_metadata or not collection_metadata.get('metadatas'):
                        print("Warning: No collection metadata available. Cannot verify repository state.")
                    else:
                        # Extract collection metadata (the first document's metadata contains collection info)
                        saved_repo_id = collection_metadata.get('metadatas', [{}])[0].get('repo_id')
                        saved_repo_path = collection_metadata.get('metadatas', [{}])[0].get('repo_path')
                        
                        # Verify repository identity
                        if saved_repo_id and saved_repo_id != self.metadata.get("repo_id"):
                            print("Warning: Vector store was created for a different repository.")
                            print(f"Current repo ID: {self.metadata.get('repo_id')}")
                            print(f"Stored repo ID: {saved_repo_id}")
                            if not force:
                                print("Use force=True to load anyway or regenerate embeddings.")
                                return False
                                
                        # Verify repo path as additional check
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
            
            # Build the path to the database directory
            db_path = os.path.join(os.path.abspath(repo_path), cls.DB_DIR)
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
