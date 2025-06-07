"""Unit tests for document generation functionality."""

from pathlib import Path

import pytest
from langdoc.application.services import DocumentationGeneratorService
from langdoc.domain.models import DocumentType


def test_readme_generation(
    sample_codebase_context, mock_llm_service, mock_vector_store, console
):
    """Test generating a README document."""
    # Arrange
    generator = DocumentationGeneratorService(
        llm_service=mock_llm_service,
        vector_store=mock_vector_store,
        console=console,
    )
    
    # Act
    document = generator.generate(DocumentType.README, sample_codebase_context)
    
    # Assert
    assert document.content
    assert document.doc_type == DocumentType.README
    assert "# LangDoc" in document.content
    assert "RAG" in document.content
    
    # Verify the LLM service was called
    mock_llm_service.generate_text.assert_called_once()
    
    # Verify the vector store was used if provided
    if mock_vector_store:
        mock_vector_store.retrieve_relevant_context.assert_called_once()


def test_readme_generation_with_options(
    sample_codebase_context, mock_llm_service, console
):
    """Test generating a README document with specific options."""
    # Arrange
    generator = DocumentationGeneratorService(
        llm_service=mock_llm_service,
        console=console,
    )
    options = {"include_badges": "true", "include_toc": "true"}
    
    # Act
    document = generator.generate(
        DocumentType.README, sample_codebase_context, options
    )
    
    # Assert
    assert document.content
    assert document.doc_type == DocumentType.README
    
    # Verify the LLM service was called with the correct options
    mock_llm_service.generate_text.assert_called_once()


def test_generate_other_document_type(
    sample_codebase_context, mock_llm_service, console
):
    """Test generating a non-README document."""
    # Arrange
    generator = DocumentationGeneratorService(
        llm_service=mock_llm_service,
        console=console,
    )
    
    # Act
    document = generator.generate(DocumentType.ARCHITECTURE, sample_codebase_context)
    
    # Assert
    assert document.content
    assert document.doc_type == DocumentType.ARCHITECTURE
    
    # Verify the LLM service was called
    mock_llm_service.generate_text.assert_called_once()
