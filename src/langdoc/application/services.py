"""Application services implementing use cases."""

from pathlib import Path
from typing import Dict, List, Optional

import rich.console
from langdoc.domain.interfaces import (
    CodebaseAnalyzer,
    DocumentGenerator,
    FileSystem,
    GitRepository,
    LLMService,
    VectorStore,
)
from langdoc.domain.models import CodebaseContext, DocumentType, GeneratedDocument


class CodebaseAnalysisService(CodebaseAnalyzer):
    """Service for analyzing a codebase and extracting context."""

    def __init__(
        self,
        filesystem: FileSystem,
        git_service: GitRepository,
        vector_store: Optional[VectorStore] = None,
        console: Optional[rich.console.Console] = None,
    ):
        """Initialize the codebase analysis service.

        Args:
            filesystem: FileSystem implementation
            git_service: GitRepository implementation
            vector_store: Optional VectorStore implementation
            console: Optional Rich console for output
        """
        self.filesystem = filesystem
        self.git_service = git_service
        self.vector_store = vector_store
        self.console = console or rich.console.Console()

    def analyze(self, codebase_path: Path) -> CodebaseContext:
        """Analyze a codebase and extract contextual information.

        Args:
            codebase_path: Path to the codebase root directory

        Returns:
            CodebaseContext containing extracted information about the codebase
        """
        self.console.print(f"[green]Analyzing codebase:[/green] {codebase_path}")

        # Extract project structure
        structure = self.filesystem.analyze_project_structure(codebase_path)
        
        # Extract Git repository information
        git_info = self.git_service.extract_project_info(codebase_path)
        
        # Determine project name from Git information or directory name
        if "repo_name" in git_info:
            project_name = git_info["repo_name"]
        else:
            project_name = codebase_path.name
            
        # Check for project description in pyproject.toml or setup.py
        project_description = None
        pyproject_path = codebase_path / "pyproject.toml"
        setup_path = codebase_path / "setup.py"
        
        if pyproject_path.exists():
            # Very simple parsing of pyproject.toml
            try:
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for line in content.splitlines():
                        if "description" in line and "=" in line:
                            project_description = line.split("=", 1)[1].strip().strip('"\'')
                            break
            except Exception as e:
                self.console.print(f"[yellow]Error reading pyproject.toml:[/yellow] {str(e)}")
        
        elif setup_path.exists():
            # Very simple parsing of setup.py
            try:
                with open(setup_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for line in content.splitlines():
                        if "description" in line and "=" in line:
                            project_description = line.split("=", 1)[1].strip().strip('"\'')
                            break
            except Exception as e:
                self.console.print(f"[yellow]Error reading setup.py:[/yellow] {str(e)}")
        
        # Check for CLI (presence of typer, click, or argparse usage)
        has_cli = False
        cli_commands = {}
        
        # Look for evidence of CLI in Python files
        python_files = []
        for dir_name, files in structure.items():
            python_files.extend([
                file for file in files 
                if file.endswith(".py") and not file.startswith("_")
            ])
        
        # Look for specific files that might indicate CLI presence
        cli_indicators = ["cli.py", "main.py", "__main__.py", "app.py", "command.py"]
        for indicator in cli_indicators:
            for dir_name, files in structure.items():
                if any(file.endswith(indicator) for file in files):
                    has_cli = True
                    break
            if has_cli:
                break
        
        # Extract dependencies from requirements.txt or pyproject.toml
        dependencies = []
        req_path = codebase_path / "requirements.txt"
        
        if req_path.exists():
            try:
                with open(req_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            dependencies.append(line)
            except Exception as e:
                self.console.print(f"[yellow]Error reading requirements.txt:[/yellow] {str(e)}")
        
        elif pyproject_path.exists():
            try:
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    dep_section = False
                    for line in content.splitlines():
                        if "[dependencies]" in line or "[project.dependencies]" in line:
                            dep_section = True
                        elif dep_section and line.strip().startswith("["):
                            dep_section = False
                        elif dep_section and "=" in line:
                            dep = line.strip()
                            dependencies.append(dep)
            except Exception as e:
                self.console.print(f"[yellow]Error reading dependencies from pyproject.toml:[/yellow] {str(e)}")
        
        # Create CodebaseContext
        context = CodebaseContext(
            project_name=project_name,
            project_description=project_description,
            project_structure=structure,
            dependencies=dependencies,
            has_cli=has_cli,
            cli_commands=cli_commands,
            has_tests="tests" in structure
        )
        
        return context


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
                query = f"Project {context.project_name} overview, purpose, features and usage"
            else:
                query = f"Project {context.project_name} {doc_type.value}"
                
            self.console.print(f"[green]Retrieving relevant context for {doc_type.value}...[/green]")
            vector_context = self.vector_store.retrieve_relevant_context(query, max_documents=5)
        
        # Generate documentation based on type
        if doc_type == DocumentType.README:
            content = self._generate_readme(context, vector_context, options)
        else:
            # Generic document generation
            content = self._generate_generic_doc(doc_type, context, vector_context, options)
            
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
        from langdoc.infrastructure.llm.llm_service import ReadmeGenerationLLMService
        
        # Check if the LLM service is already a ReadmeGenerationLLMService
        if isinstance(self.llm_service, ReadmeGenerationLLMService):
            readme_generator = self.llm_service
        else:
            # Create a specialized README generator
            readme_generator = ReadmeGenerationLLMService()
        
        # Extract Git information
        git_info = {}
        
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
            context=vector_context
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
        Generate documentation of type '{doc_type.value}' for the project '{context.project_name}'.
        
        Project Description: {context.project_description or "Not provided"}
        
        The documentation should be comprehensive, accurate, and follow best practices.
        Format the documentation using Markdown.
        """
        
        return self.llm_service.generate_text(prompt, vector_context)
