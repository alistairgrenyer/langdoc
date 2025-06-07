"""Vector store implementation for code embeddings."""

import glob
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import rich.console
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain_community.vectorstores import Chroma


class CodeVectorStore:
    """Vector store for code embeddings using LangChain and ChromaDB."""

    def __init__(
        self,
        persist_directory: Optional[Union[str, Path]] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        console: Optional[rich.console.Console] = None,
    ):
        """Initialize the code vector store.

        Args:
            persist_directory: Directory to persist the vector store
            embedding_model: Name of the HuggingFace embedding model to use
            console: Optional Rich console for output
        """
        self.console = console or rich.console.Console()
        
        # Setup persist directory
        if persist_directory is None:
            home = Path.home()
            persist_directory = home / ".langdoc" / "vectorstore"
        elif isinstance(persist_directory, str):
            persist_directory = Path(persist_directory)
            
        self.persist_directory = persist_directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        
        # Initialize vector store
        self._initialize_vector_store()
        
    def _initialize_vector_store(self) -> None:
        """Initialize or load the vector store."""
        if list(self.persist_directory.glob("*")):
            self.console.print("[green]Loading existing vector store...[/green]")
            self.vector_store = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings
            )
        else:
            self.console.print("[yellow]Initializing new vector store...[/yellow]")
            self.vector_store = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings
            )

    def index_codebase(
        self, codebase_path: Path, exclude_patterns: Optional[List[str]] = None
    ) -> None:
        """Index a codebase for vector search.

        Args:
            codebase_path: Path to the codebase root directory
            exclude_patterns: Optional list of glob patterns to exclude
        """
        exclude_patterns = exclude_patterns or []
        
        # Add common exclusion patterns
        default_excludes = [
            ".git", ".github", "__pycache__", "*.pyc", ".pytest_cache",
            ".coverage", "htmlcov", ".vscode", ".idea", "venv", ".env*",
            "*.jpg", "*.png", "*.svg", "*.pdf", "*.zip", "*.gz", "*.tar"
        ]
        exclude_patterns.extend(default_excludes)
        
        # Read .gitignore for additional exclude patterns if it exists
        gitignore_path = codebase_path / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8") as f:
                gitignore_patterns = [
                    line.strip() for line in f
                    if line.strip() and not line.strip().startswith("#")
                ]
            exclude_patterns.extend(gitignore_patterns)
        
        # Process files
        documents = []
        processed_count = 0
        
        # Find all text files in the codebase
        all_files = []
        for root, _, files in os.walk(str(codebase_path)):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        # Filter files by common text file extensions
        text_extensions = [
            ".py", ".js", ".ts", ".html", ".css", ".md", ".rst", ".txt",
            ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".conf"
        ]
        text_files = [
            f for f in all_files 
            if os.path.splitext(f)[1].lower() in text_extensions
        ]
        
        # Filter out excluded files
        for file_path in text_files:
            rel_path = os.path.relpath(file_path, str(codebase_path))
            
            # Check if file should be excluded
            should_exclude = False
            for pattern in exclude_patterns:
                if glob.fnmatch.fnmatch(rel_path, pattern):
                    should_exclude = True
                    break
                    
            if should_exclude:
                continue
                
            # Read file content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Skip empty files
                if not content.strip():
                    continue
                    
                # Create document
                document = Document(
                    page_content=content,
                    metadata={
                        "source": rel_path,
                        "path": file_path,
                        "type": os.path.splitext(file_path)[1][1:],  # Extension without dot
                    }
                )
                documents.append(document)
                processed_count += 1
                
            except Exception as e:
                self.console.print(f"[yellow]Error processing file {rel_path}:[/yellow] {str(e)}")
                
        # Add documents to vector store
        self.console.print(f"[green]Adding {processed_count} files to vector store...[/green]")
        if documents:
            self.vector_store.add_documents(documents)
            self.vector_store.persist()
            self.console.print("[green]Vector store updated and persisted.[/green]")
        else:
            self.console.print("[yellow]No documents to add to vector store.[/yellow]")

    def retrieve_relevant_context(
        self, query: str, max_documents: int = 5
    ) -> List[Dict[str, str]]:
        """Retrieve relevant context based on a query.

        Args:
            query: The query to search for relevant context
            max_documents: Maximum number of documents to retrieve

        Returns:
            List of relevant documents with content and metadata
        """
        results = self.vector_store.similarity_search(query, k=max_documents)
        
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "type": doc.metadata.get("type", "unknown"),
            }
            for doc in results
        ]
