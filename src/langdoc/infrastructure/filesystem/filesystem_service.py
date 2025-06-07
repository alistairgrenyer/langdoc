"""Filesystem service implementation."""

from pathlib import Path
from typing import Dict, List, Optional

import rich.console
from langdoc.domain.models import DocumentType, GeneratedDocument


class FilesystemService:
    """Implementation of filesystem operations."""

    def __init__(self, console: Optional[rich.console.Console] = None):
        """Initialize the filesystem service.

        Args:
            console: Optional Rich console for output
        """
        self.console = console or rich.console.Console()

    def write_document(self, document: GeneratedDocument, output_path: Path) -> Path:
        """Write a generated document to the filesystem.

        Args:
            document: The document to write
            output_path: Path where to write the document

        Returns:
            Path to the written document
        """
        # If output_path is a directory, determine filename based on document type
        if output_path.is_dir():
            if document.doc_type == DocumentType.README:
                file_path = output_path / "README.md"
            else:
                file_path = output_path / f"{document.doc_type.value}.md"
        else:
            file_path = output_path

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        file_path.write_text(document.content, encoding="utf-8")
        
        self.console.print(f"[green]Document written to:[/green] {file_path}")
        return file_path

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
        exclude_patterns = exclude_patterns or []
        
        # Add common exclusion patterns
        default_excludes = [
            ".git", ".github", "__pycache__", "*.pyc", ".pytest_cache",
            ".coverage", "htmlcov", ".vscode", ".idea", "venv", ".env*"
        ]
        exclude_patterns.extend(default_excludes)
        
        # Read .gitignore for additional exclude patterns
        gitignore_path = project_path / ".gitignore"
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_patterns = [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
        exclude_patterns.extend(gitignore_patterns)
            
        # Build structure dictionary
        structure: Dict[str, List[str]] = {}
        
        # Check for key directories
        for dir_name in ["src", "tests", "docs"]:
            dir_path = project_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                structure[dir_name] = self._list_directory_contents(
                    dir_path, project_path, exclude_patterns
                )
        
        # Check for key files
        for file_name in ["README.md", "pyproject.toml", "requirements.txt", "setup.py"]:
            file_path = project_path / file_name
            if file_path.exists() and file_path.is_file():
                if "root_files" not in structure:
                    structure["root_files"] = []
                structure["root_files"].append(file_name)
        
        return structure
        
    def _list_directory_contents(
        self, 
        directory: Path, 
        base_path: Path,
        exclude_patterns: List[str],
        max_depth: int = 3
    ) -> List[str]:
        """List contents of a directory recursively up to max_depth.
        
        Args:
            directory: Directory to list contents of
            base_path: Base project path for creating relative paths
            exclude_patterns: Patterns to exclude
            max_depth: Maximum depth to recurse
            
        Returns:
            List of paths relative to base_path
        """
        if max_depth <= 0:
            return []
            
        results = []
        
        try:
            for path in directory.iterdir():
                # Create relative path for pattern matching
                rel_path = str(path.relative_to(base_path))
                
                # Check if path should be excluded
                if any(path.match(pattern) for pattern in exclude_patterns):
                    continue
                    
                if path.is_file():
                    results.append(rel_path)
                elif path.is_dir():
                    # Add directory
                    results.append(f"{rel_path}/")
                    # Recursively add subdirectory contents
                    if max_depth > 1:
                        sub_contents = self._list_directory_contents(
                            path, base_path, exclude_patterns, max_depth - 1
                        )
                        results.extend(sub_contents)
        except PermissionError:
            self.console.print(f"[yellow]Permission error reading directory:[/yellow] {directory}")
            
        return results
