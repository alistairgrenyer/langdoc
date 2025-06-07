"""Codebase analysis service implementation."""

from pathlib import Path
from typing import Optional

import rich.console

from langdoc.domain.interfaces import (
    CodebaseAnalyzer,
    FileSystem,
    GitRepository,
    VectorStore,
)
from langdoc.domain.models import CodebaseContext


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
        
        # Determine project name from Git information
        project_name = git_info["repo_name"]
            
        # Check for project description in pyproject.toml or setup.py
        project_description = None
        pyproject_path = codebase_path / "pyproject.toml"
        setup_path = codebase_path / "setup.py"
        
        if pyproject_path.exists():
            # Very simple parsing of pyproject.toml
            try:
                with open(pyproject_path, encoding="utf-8") as f:
                    content = f.read()
                    for line in content.splitlines():
                        if "description" in line and "=" in line:
                            project_description = line.split("=", 1)[1].strip().strip('"\'')
                            break
            except Exception as e:
                self.console.print(
                    f"[yellow]Error reading pyproject.toml:[/yellow] {str(e)}",
                )
        
        elif setup_path.exists():
            # Very simple parsing of setup.py
            try:
                with open(
                    setup_path, encoding="utf-8"
                ) as f:
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
        for _, files in structure.items():
            python_files.extend([
                file for file in files 
                if file.endswith(".py") and not file.startswith("_")
            ])
        
        # Look for specific files that might indicate CLI presence
        cli_indicators = ["cli.py", "main.py", "__main__.py", "app.py", "command.py"]
        for indicator in cli_indicators:
            for _, files in structure.items():
                if any(file.endswith(indicator) for file in files):
                    has_cli = True
                    break
            if has_cli:
                break
        
        # Check for specific imports that indicate CLI usage
        if not has_cli:
            cli_libraries = ["typer", "click", "argparse"]
            for dir_name, files in structure.items():
                for file in files:
                    if not file.endswith(".py"):
                        continue
                    
                    try:
                        file_path = codebase_path / dir_name / file
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()
                            
                            for lib in cli_libraries:
                                if lib in content.lower():
                                    has_cli = True
                                    cli_commands.append(file)
                    except Exception:
                        # Skip files that can't be read
                        continue
                    
                    if has_cli:
                        break
                if has_cli:
                    break
        
        # Extract dependencies from pyproject.toml or requirements.txt
        dependencies = []
        
        # Check pyproject.toml first
        if pyproject_path.exists():
            try:
                with open(pyproject_path, encoding="utf-8") as f:
                    content = f.read()
                    in_dependencies = False
                    
                    for line in content.splitlines():
                        if "[dependencies]" in line or "[project.dependencies]" in line:
                            in_dependencies = True
                            continue
                        
                        if (in_dependencies and 
                            line.strip() and 
                            not line.strip().startswith("[")):
                            # Extract dependency name
                            dep = (
                                line.strip().split("=")[0].strip().strip('"\'')
                            )
                            dependencies.append(dep)
                        
                        # Exit the dependencies section
                        if (in_dependencies and 
                            line.strip().startswith("[") and 
                            not any(x in line for x in [
                                "[dependencies]", 
                                "[project.dependencies]",
                            ])):
                            in_dependencies = False
            except Exception as e:
                self.console.print(f"[yellow]Error reading dependencies from pyproject.toml:[/yellow] {str(e)}")
        
        # Check requirements.txt as fallback
        if not dependencies:
            req_path = codebase_path / "requirements.txt"
            if req_path.exists():
                try:
                    with open(req_path, encoding="utf-8") as f:
                        for req_line in f:
                            req_line_content = req_line.strip()
                            if req_line_content and not req_line_content.startswith("#"):
                                # Extract package name (remove version specifiers)
                                package = (
                                    req_line_content.split("==")[0]
                                    .split(">=")[0]
                                    .split("<=")[0].strip()
                                )
                                dependencies.append(package)
                except Exception as e:
                    self.console.print(
                    f"[yellow]Error reading requirements.txt:[/yellow] {str(e)}",
                )
        
        # Check for tests
        has_tests = False
        for dir_name in structure:
            if "test" in dir_name.lower():
                has_tests = True
                break
        
        # Create and return the codebase context
        return CodebaseContext(
            project_name=project_name,
            project_description=project_description,
            project_structure=structure,
            dependencies=dependencies,
            has_cli=has_cli,
            cli_commands=cli_commands,
            has_tests=has_tests,
            git_info=git_info,
        )
