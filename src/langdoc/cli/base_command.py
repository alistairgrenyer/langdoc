"""Base command implementation for CLI commands."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

import rich.console


class Command(ABC):
    """Base command class for CLI commands."""

    def __init__(self, console: Optional[rich.console.Console] = None):
        """Initialize the command.
        
        Args:
            console: Optional Rich console for output
        """
        self.console = console or rich.console.Console()

    @abstractmethod
    def execute(self, **kwargs) -> Dict:
        """Execute the command.
        
        Args:
            **kwargs: Command-specific arguments
            
        Returns:
            Dictionary with command results
        """
        pass

    def validate_path(self, path: str) -> Path:
        """Validate and convert a path string to a Path object.
        
        Args:
            path: Path string to validate
            
        Returns:
            Path object if valid
            
        Raises:
            ValueError: If path is invalid or doesn't exist
        """
        try:
            path_obj = Path(path).resolve()
            if not path_obj.exists():
                raise ValueError(f"Path does not exist: {path}")
            return path_obj
        except Exception as e:
            self.console.print(f"[red]Error validating path:[/red] {str(e)}")
            raise ValueError(f"Invalid path: {path}")
