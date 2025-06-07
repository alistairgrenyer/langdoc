"""Document processor for code files."""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from langchain.schema import Document
from rich.console import Console


class DocumentProcessor:
    """Processor for extracting documents from code files."""

    # Extensions considered as text files for indexing
    TEXT_EXTENSIONS: Set[str] = {
        ".py", ".js", ".ts", ".html", ".css", ".md", ".rst", ".json", ".yaml",
        ".yml", ".toml", ".ini", ".sh", ".bat", ".txt", ".sql", ".c", ".cpp",
        ".h", ".hpp", ".java", ".rb", ".go", ".rs", ".php", ".cs", ".jsx",
        ".tsx", ".vue", ".scss", ".sass", ".less", ".xml", ".csv",
    }
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the document processor.
        
        Args:
            console: Optional Rich console for output
        """
        self.console = console or Console()
    
    def get_git_documents(
        self, 
        codebase_path: Path,
    ) -> Tuple[List[Document], int, int]:
        """Get document list using Git for tracking files.
        
        Args:
            codebase_path: Path to the codebase root directory
            
        Returns:
            Tuple containing documents list, processed count, and skipped count
        """
        # Use Git to list all tracked files
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(codebase_path),
            capture_output=True,
            text=True,
            check=True,
        )
        
        # Get the list of tracked files
        git_files = result.stdout.strip()
        tracked_files = git_files.split("\n")
        
        self.console.print(f"Found {len(tracked_files)} tracked files in Git repository")
        
        # Get only text files
        text_files = [
            os.path.join(str(codebase_path), file)
            for file in tracked_files
            if os.path.splitext(file)[1].lower() in self.TEXT_EXTENSIONS
        ]
        
        skipped_count = len(tracked_files) - len(text_files)
        self.console.print(
            f"Found {len(text_files)} text files to process "
            f"(skipped {skipped_count} non-text files)"
        )
        
        # Process documents
        documents = []
        processed_count = 0
        additional_skipped = 0
        
        for file_path in text_files:
            # Get relative path for reporting
            rel_path = os.path.relpath(file_path, str(codebase_path))
                
            # Read file content
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    
                # Skip empty files
                if not content.strip():
                    additional_skipped += 1
                    continue
                    
                # Create document
                document = Document(
                    page_content=content,
                    metadata={
                        "source": rel_path,
                        "path": file_path,
                        "type": os.path.splitext(file_path)[1][1:],  # Extension without dot
                    },
                )
                documents.append(document)
                processed_count += 1
                
            except Exception as e:
                self.console.print(
                    f"[yellow]Error processing file {rel_path}:[/yellow] {str(e)}"
                )
                additional_skipped += 1
        
        # Return processed documents and statistics
        return documents, processed_count, skipped_count + additional_skipped
