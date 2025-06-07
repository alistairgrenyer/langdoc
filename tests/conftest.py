"""Test configuration and fixtures for LangDoc."""

import os
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from src.langdoc.domain.interfaces import GitRepository, LLMService, VectorStore
from src.langdoc.domain.models import CodebaseContext, DocumentType, GeneratedDocument
from src.langdoc.infrastructure.filesystem.filesystem_service import FilesystemService
from src.langdoc.infrastructure.git.git_service import GitRepositoryService


@pytest.fixture
def console():
    """Fixture for a Rich console that doesn't print to stdout."""
    return Console(file=open(os.devnull, "w"))


@pytest.fixture
def sample_project_structure():
    """Fixture for a sample project structure."""
    return {
        "src": [
            "src/langdoc/",
            "src/langdoc/__init__.py",
            "src/langdoc/cli/",
            "src/langdoc/cli/app.py",
            "src/langdoc/application/",
            "src/langdoc/domain/",
            "src/langdoc/infrastructure/",
        ],
        "tests": [
            "tests/",
            "tests/unit/",
            "tests/integration/",
        ],
        "docs": [
            "docs/",
            "docs/adr/",
        ],
        "root_files": [
            "README.md",
            "pyproject.toml",
            "requirements.txt",
            ".gitignore",
        ],
    }


@pytest.fixture
def sample_codebase_context(sample_project_structure):
    """Fixture for a sample codebase context."""
    return CodebaseContext(
        project_name="langdoc",
        project_description="Auto-generate documentation for codebases using LLMs and RAG",
        project_structure=sample_project_structure,
        main_features=["README generation", "RAG-based documentation"],
        dependencies=["langchain", "typer", "rich"],
        has_cli=True,
        cli_commands={"langdoc readme": "Generate a README.md file"},
        has_tests=True,
    )


@pytest.fixture
def mock_git_service():
    """Fixture for a mocked GitRepository."""
    mock = MagicMock(spec=GitRepository)
    mock.extract_project_info.return_value = {
        "is_git_repo": "true",
        "remote_url": "https://github.com/username/langdoc",
        "repo_name": "langdoc",
        "repo_owner": "username",
        "default_branch": "main",
    }
    return mock


@pytest.fixture
def mock_llm_service():
    """Fixture for a mocked LLMService."""
    mock = MagicMock(spec=LLMService)
    mock.generate_text.return_value = """# LangDoc

A Python tool to auto-generate documentation for codebases using LLMs and RAG.

## Installation

```
pip install langdoc
```

## Usage

```
langdoc readme --path /path/to/your/project
```

## Features

- Generate README files that feel human-written
- Uses RAG for context-aware documentation

## License

MIT
"""
    return mock


@pytest.fixture
def mock_vector_store():
    """Fixture for a mocked VectorStore."""
    mock = MagicMock(spec=VectorStore)
    mock.retrieve_relevant_context.return_value = [
        {
            "content": "Auto-generate documentation for codebases using LLMs and RAG.",
            "source": "src/langdoc/__init__.py",
            "type": "py",
        }
    ]
    return mock


@pytest.fixture
def tmp_project_dir(tmp_path):
    """Create a temporary project directory structure."""
    # Create directories
    (tmp_path / "src" / "langdoc" / "cli").mkdir(parents=True)
    (tmp_path / "src" / "langdoc" / "domain").mkdir(parents=True)
    (tmp_path / "src" / "langdoc" / "application").mkdir(parents=True)
    (tmp_path / "src" / "langdoc" / "infrastructure").mkdir(parents=True)
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)

    # Create sample files
    (tmp_path / "src" / "langdoc" / "__init__.py").write_text(
        '"""LangDoc: Auto-generate documentation for codebases."""\n\n__version__ = "0.1.0"'
    )
    (tmp_path / "src" / "langdoc" / "cli" / "app.py").write_text(
        '"""CLI application."""\n\nimport typer\n\napp = typer.Typer()'
    )
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'langdoc'\ndescription = 'Documentation generator'")
    (tmp_path / "README.md").write_text("# LangDoc\n\nPlaceholder README")
    
    return tmp_path


@pytest.fixture
def filesystem_service(console):
    """Fixture for a real FilesystemService."""
    return FilesystemService(console=console)


@pytest.fixture
def git_service_mock():
    """Fixture for a mocked GitRepositoryService."""
    mock = MagicMock(spec=GitRepositoryService)
    mock.extract_project_info.return_value = {
        "is_git_repo": "true",
        "remote_url": "https://github.com/username/langdoc.git",
        "repo_name": "langdoc",
        "repo_owner": "username",
        "default_branch": "main",
    }
    return mock
