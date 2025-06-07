"""Unit tests for codebase analysis functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langdoc.application.services import CodebaseAnalysisService


def test_codebase_analysis(tmp_project_dir, filesystem_service, git_service_mock, console):
    """Test analyzing a codebase."""
    # Arrange
    analyzer = CodebaseAnalysisService(
        filesystem=filesystem_service,
        git_service=git_service_mock,
        console=console,
    )
    
    # Act
    context = analyzer.analyze(tmp_project_dir)
    
    # Assert
    assert context.project_name == "langdoc"
    assert "Documentation generator" in context.project_description
    assert "src" in context.project_structure
    assert context.has_cli  # Should detect CLI from app.py
    
    # Verify the git service was called
    git_service_mock.extract_project_info.assert_called_once_with(tmp_project_dir)


def test_analyze_detects_dependencies(tmp_project_dir, filesystem_service, git_service_mock, console):
    """Test that analysis detects project dependencies."""
    # Arrange
    # Add requirements.txt
    requirements_content = """
langchain>=0.0.200
typer>=0.7.0
rich>=13.0.0
openai>=1.0.0
chromadb>=0.4.0
"""
    (tmp_project_dir / "requirements.txt").write_text(requirements_content)
    
    analyzer = CodebaseAnalysisService(
        filesystem=filesystem_service,
        git_service=git_service_mock,
        console=console,
    )
    
    # Act
    context = analyzer.analyze(tmp_project_dir)
    
    # Assert
    assert context.dependencies
    assert any("langchain" in dep for dep in context.dependencies)
    assert any("typer" in dep for dep in context.dependencies)


def test_analyze_with_non_git_repo(tmp_project_dir, filesystem_service, console):
    """Test analyzing a non-Git repository."""
    # Arrange
    git_service = MagicMock()
    git_service.extract_project_info.return_value = {"is_git_repo": "false"}
    
    analyzer = CodebaseAnalysisService(
        filesystem=filesystem_service,
        git_service=git_service,
        console=console,
    )
    
    # Act
    context = analyzer.analyze(tmp_project_dir)
    
    # Assert
    assert context.project_name == tmp_project_dir.name
    assert "src" in context.project_structure
