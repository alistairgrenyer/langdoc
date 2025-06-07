"""Domain models for LangDoc."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class DocumentType(Enum):
    """Types of documents that can be generated."""

    README = "readme"
    ARCHITECTURE = "architecture"
    API_DOCS = "api_docs"


@dataclass
class CodebaseContext:
    """Represents the analyzed context of a codebase."""

    project_name: str
    project_description: Optional[str] = None
    project_structure: Optional[Dict[str, List[str]]] = None
    main_features: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    has_cli: bool = False
    cli_commands: Optional[Dict[str, str]] = None
    has_tests: bool = False
    git_info: Dict[str, str] = None


@dataclass
class DocumentationRequest:
    """Request for generating documentation."""

    doc_type: DocumentType
    codebase_path: str
    output_path: Optional[str] = None
    options: Optional[Dict[str, str]] = None


@dataclass
class GeneratedDocument:
    """Represents a generated documentation document."""

    content: str
    doc_type: DocumentType
    path: Optional[str] = None
