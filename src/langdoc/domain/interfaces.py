"""Domain interfaces for LangDoc."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Protocol

from langdoc.domain.models import CodebaseContext, DocumentType, GeneratedDocument


class CodebaseAnalyzer(Protocol):
    """Protocol for analyzing a codebase and extracting context."""

    @abstractmethod
    def analyze(self, codebase_path: Path) -> CodebaseContext:
        """Analyze a codebase and extract contextual information.

        Args:
            codebase_path: Path to the codebase root directory

        Returns:
            CodebaseContext containing extracted information about the codebase
        """
        ...


class DocumentGenerator(Protocol):
    """Protocol for document generators."""

    @abstractmethod
    def generate(
        self,
        doc_type: DocumentType,
        context: CodebaseContext,
        options: Optional[Dict[str, str]] = None,
    ) -> GeneratedDocument:
        """Generate documentation based on codebase context.

        Args:
            doc_type: Type of documentation to generate
            context: Context information about the codebase
            options: Optional generation parameters

        Returns:
            Generated documentation content as a GeneratedDocument
        """
        ...


class VectorStore(Protocol):
    """Protocol for vector stores used in RAG."""

    @abstractmethod
    def index_codebase(
        self, codebase_path: Path, exclude_patterns: Optional[List[str]] = None
    ) -> None:
        """Index a codebase for vector search.

        Args:
            codebase_path: Path to the codebase root directory
            exclude_patterns: Optional list of glob patterns to exclude
        """
        ...

    @abstractmethod
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
        ...


class LLMService(Protocol):
    """Protocol for LLM services."""

    @abstractmethod
    def generate_text(
        self, prompt: str, context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate text using an LLM.

        Args:
            prompt: The prompt to send to the LLM
            context: Optional context to include with the prompt

        Returns:
            Generated text from the LLM
        """
        ...


class GitRepository(Protocol):
    """Protocol for Git repository operations."""

    @abstractmethod
    def extract_project_info(self, repo_path: Path) -> Dict[str, str]:
        """Extract information from a Git repository.

        Args:
            repo_path: Path to the Git repository

        Returns:
            Dictionary containing repository information
        """
        ...


class FileSystem(Protocol):
    """Protocol for filesystem operations."""

    @abstractmethod
    def write_document(self, document: GeneratedDocument, output_path: Path) -> Path:
        """Write a generated document to the filesystem.

        Args:
            document: The document to write
            output_path: Path where to write the document

        Returns:
            Path to the written document
        """
        ...

    @abstractmethod
    def analyze_project_structure(
        self, project_path: Path, exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """Analyze the structure of a project.

        Args:
            project_path: Path to the project
            exclude_patterns: Optional list of glob patterns to exclude

        Returns:
            Dictionary representing the project structure
        """
        ...
