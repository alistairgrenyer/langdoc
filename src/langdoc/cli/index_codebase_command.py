"""Index codebase command implementation."""

from pathlib import Path
from typing import Dict, List, Optional

from langdoc.cli.base_command import Command
from langdoc.domain.interfaces import VectorStore


class IndexCodebaseCommand(Command):
    """Command to index a codebase into the vector store."""

    def __init__(
        self,
        vector_store: VectorStore,
        console=None,
    ):
        """Initialize the index codebase command.
        
        Args:
            vector_store: Vector store service
            console: Optional Rich console for output
        """
        super().__init__(console)
        self.vector_store = vector_store

    def execute(
        self,
        path: str,
        exclude: Optional[List[str]] = None,
    ) -> Dict:
        """Execute the index codebase command.
        
        Args:
            path: Path to the codebase
            exclude: Optional list of glob patterns to exclude
            
        Returns:
            Dictionary with command results
        """
        # Validate path
        codebase_path = self.validate_path(path)
        
        # Index codebase
        self.console.print(f"Indexing codebase: {codebase_path}")
        
        if exclude:
            self.console.print(f"Excluding patterns: {', '.join(exclude)}")
            
        # Perform indexing
        stats = self.vector_store.index_codebase(
            codebase_path=codebase_path,
            exclude_patterns=exclude,
        )
        
        # Report results
        self.console.print(
            f"[green]Indexing complete:[/green] "
            f"Processed {stats['processed']} files, "
            f"Indexed {stats['indexed']} files, "
            f"Skipped {stats['skipped']} files"
        )
        
        return {
            "success": True,
            "stats": stats,
        }
