"""CLI commands implementing the Command pattern."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

import rich.console
from langdoc.domain.models import CodebaseContext, DocumentType, GeneratedDocument
from langdoc.application.services import CodebaseAnalysisService, DocumentationGeneratorService


class Command(ABC):
    """Base command interface following the Command pattern."""

    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass


class GenerateReadmeCommand(Command):
    """Command for generating a README file."""

    def __init__(
        self,
        analyzer: CodebaseAnalysisService,
        generator: DocumentationGeneratorService,
        codebase_path: Path,
        output_path: Optional[Path] = None,
        options: Optional[Dict[str, str]] = None,
        console: Optional[rich.console.Console] = None,
    ):
        """Initialize the generate README command.

        Args:
            analyzer: Codebase analyzer service
            generator: Documentation generator service
            codebase_path: Path to the codebase
            output_path: Optional output path for the README
            options: Optional generation parameters
            console: Optional Rich console for output
        """
        self.analyzer = analyzer
        self.generator = generator
        self.codebase_path = codebase_path
        self.output_path = output_path or codebase_path
        self.options = options or {}
        self.console = console or rich.console.Console()

    def execute(self) -> Path:
        """Execute the generate README command.

        Returns:
            Path to the generated README file
        """
        self.console.print(f"[bold green]Generating README for:[/bold green] {self.codebase_path}")
        
        # Step 1: Analyze the codebase
        self.console.print("[bold]Step 1/3:[/bold] Analyzing codebase...")
        context = self.analyzer.analyze(self.codebase_path)
        
        # Step 2: Generate the README
        self.console.print("[bold]Step 2/3:[/bold] Generating README content...")
        document = self.generator.generate(DocumentType.README, context, self.options)
        
        # Step 3: Write the README to file
        self.console.print("[bold]Step 3/3:[/bold] Writing README to file...")
        output_file = self.output_path / "README.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(document.content)
        
        self.console.print(f"[bold green]README generated successfully![/bold green] Path: {output_file}")
        return output_file


class IndexCodebaseCommand(Command):
    """Command for indexing a codebase into the vector store."""

    def __init__(
        self,
        vector_store,
        codebase_path: Path,
        exclude_patterns: Optional[List[str]] = None,
        console: Optional[rich.console.Console] = None,
    ):
        """Initialize the index codebase command.

        Args:
            vector_store: Vector store for indexing
            codebase_path: Path to the codebase
            exclude_patterns: Optional patterns to exclude
            console: Optional Rich console for output
        """
        self.vector_store = vector_store
        self.codebase_path = codebase_path
        self.exclude_patterns = exclude_patterns or []
        self.console = console or rich.console.Console()

    def execute(self) -> None:
        """Execute the index codebase command."""
        self.console.print(f"[bold green]Indexing codebase:[/bold green] {self.codebase_path}")
        
        # Index the codebase
        self.vector_store.index_codebase(self.codebase_path, self.exclude_patterns)
        
        self.console.print("[bold green]Codebase indexed successfully![/bold green]")
