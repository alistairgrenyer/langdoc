"""Generate README command implementation."""

import os
from pathlib import Path
from typing import Dict, Optional

from langdoc.cli.base_command import Command
from langdoc.domain.interfaces import CodebaseAnalyzer, DocumentGenerator
from langdoc.domain.models import DocumentType


class GenerateReadmeCommand(Command):
    """Command to generate a README file for a codebase."""

    def __init__(
        self,
        analyzer: CodebaseAnalyzer,
        generator: DocumentGenerator,
        console=None,
    ):
        """Initialize the generate readme command.
        
        Args:
            analyzer: Codebase analyzer service
            generator: Documentation generator service
            console: Optional Rich console for output
        """
        super().__init__(console)
        self.analyzer = analyzer
        self.generator = generator

    def execute(
        self,
        path: str,
        output: Optional[str] = None,
        force: bool = False,
    ) -> Dict:
        """Execute the generate readme command.
        
        Args:
            path: Path to the codebase
            output: Optional output file path
            force: Whether to overwrite existing README
            
        Returns:
            Dictionary with command results
        """
        # Validate path
        codebase_path = self.validate_path(path)
        
        # Determine output path
        if output:
            output_path = Path(output)
        else:
            output_path = codebase_path / "README.md"
            
        # Check if README already exists
        if output_path.exists() and not force:
            self.console.print(
                f"[yellow]README already exists at {output_path}.[/yellow] "
                f"Use --force to overwrite."
            )
            return {"success": False, "reason": "file_exists"}
            
        # Analyze codebase
        self.console.print(f"Analyzing codebase: {codebase_path}")
        context = self.analyzer.analyze(codebase_path)
        
        # Generate README
        self.console.print("Generating README...")
        document = self.generator.generate(DocumentType.README, context)
        
        # Write README to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(document.content)
            
        self.console.print(f"[green]README generated at:[/green] {output_path}")
        
        return {
            "success": True,
            "path": str(output_path),
            "content_length": len(document.content),
        }
