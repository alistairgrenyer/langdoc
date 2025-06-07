"""Documentation generator service implementation."""

from typing import Dict, List, Optional

import rich.console

from langdoc.domain.interfaces import DocumentGenerator, LLMService, VectorStore
from langdoc.domain.models import CodebaseContext, DocumentType, GeneratedDocument


class DocumentationGeneratorService(DocumentGenerator):
    """Service for generating documentation from codebase context."""

    def __init__(
        self,
        llm_service: LLMService,
        vector_store: Optional[VectorStore] = None,
        console: Optional[rich.console.Console] = None,
    ):
        """Initialize the documentation generator service.

        Args:
            llm_service: LLM service implementation
            vector_store: Optional vector store implementation
            console: Optional Rich console for output
        """
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.console = console or rich.console.Console()

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
        options = options or {}
        
        # Retrieve relevant context from vector store if available
        vector_context = None
        if self.vector_store:
            if doc_type == DocumentType.README:
                query = (f"Project {context.project_name} overview, purpose, "
                         f"features and usage")
            else:
                query = f"Project {context.project_name} {doc_type.value}"
                
            self.console.print(
                f"[green]Retrieving relevant context for {doc_type.value}...[/green]",
            )
            vector_context = self.vector_store.retrieve_relevant_context(
                query, max_documents=5,
            )
        
        # Generate documentation based on type
        if doc_type == DocumentType.README:
            content = self._generate_readme(context, vector_context, options)
        else:
            # Generic document generation
            content = self._generate_generic_doc(
                doc_type, context, vector_context, options
            )
            
        return GeneratedDocument(content=content, doc_type=doc_type)
    
    def _generate_readme(
        self,
        context: CodebaseContext,
        vector_context: Optional[List[Dict[str, str]]] = None,
        options: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generate README documentation.

        Args:
            context: Codebase context
            vector_context: Optional vector context
            options: Optional generation parameters

        Returns:
            Generated README content
        """
        from langdoc.infrastructure.llm.readme_generator_service import (
            ReadmeGenerationLLMService,
        )
        
        # Check if the LLM service is already a ReadmeGenerationLLMService
        if isinstance(self.llm_service, ReadmeGenerationLLMService):
            readme_generator = self.llm_service
        else:
            # Create a specialized README generator
            readme_generator = ReadmeGenerationLLMService()
        
        # Use Git information from context
        git_info = context.git_info
        
        # Generate README
        self.console.print("[green]Generating README.md...[/green]")
        readme_content = readme_generator.generate_readme(
            project_name=context.project_name,
            project_description=context.project_description,
            project_structure=context.project_structure or {},
            has_cli=context.has_cli,
            cli_commands=context.cli_commands,
            dependencies=context.dependencies,
            git_info=git_info,
            context=vector_context,
        )
        
        return readme_content
    
    def _generate_generic_doc(
        self,
        doc_type: DocumentType,
        context: CodebaseContext,
        vector_context: Optional[List[Dict[str, str]]] = None,
        options: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generate generic documentation.

        Args:
            doc_type: Type of documentation to generate
            context: Codebase context
            vector_context: Optional vector context
            options: Optional generation parameters

        Returns:
            Generated documentation content
        """
        prompt = f"""
        Generate documentation of type '{doc_type.value}' for the project 
        '{context.project_name}'.
        
        Project Description: {context.project_description or "Not provided"}
        
        The documentation should be comprehensive, accurate, and follow best practices.
        Format the documentation using Markdown.
        """
        
        return self.llm_service.generate_text(prompt, vector_context)
