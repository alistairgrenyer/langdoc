"""
CLI Context module for managing state and dependencies across commands.
Replaces the global variable approach with a proper context object.
"""
import os
import click
from typing import Dict, Any, Optional

from embedding import CodeEmbedder
from utils import load_config, get_config_value


class LangDocContext:
    """Context object for sharing state between CLI commands."""
    
    def __init__(self):
        self.embedder: Optional[CodeEmbedder] = None
        self.config: Dict[str, Any] = {}
        self.repo_path: str = ""
        self.file_ext: str = ".py"
        self.skip_dirs: list = []
    
    def init_from_repo_path(self, repo_path: str) -> None:
        """Initialize context from repository path."""
        self.repo_path = repo_path
        self.config = load_config(repo_path)
        self.file_ext = get_config_value(self.config, 'file_ext', '.py')
        skip_dirs_str = get_config_value(self.config, 'skip_dirs', 
                                        'tests,.git,.venv,__pycache__,node_modules,.vscode,.idea,dist,build,docs')
        self.skip_dirs = [d.strip() for d in skip_dirs_str.split(',') if d.strip()]
    
    def init_embedder(self, force_reload: bool = False) -> bool:
        """Initialize or reload the embedder with proper repository tracking.
        
        Args:
            force_reload: If True, recreate the embedder and force reload instead of using cached version
            
        Returns:
            True if vector store was successfully loaded, False otherwise
        """
        if self.embedder is None or force_reload:
            # Initialize with repository path for proper metadata tracking
            self.embedder = CodeEmbedder(repo_path=self.repo_path)
        
        # Check if Chroma database directory exists
        db_path = os.path.join(self.repo_path, self.embedder.DB_DIR)
        collection_name = self.embedder._collection_name
        collection_path = os.path.join(db_path, collection_name)
        db_exists = os.path.exists(collection_path) and os.path.exists(os.path.join(collection_path, "chroma.sqlite3"))
        
        if db_exists:
            # Try to load with metadata validation first
            if not force_reload and self.embedder.load_vector_store():
                click.echo("✅ Successfully loaded existing embeddings for repository.")
                return True
                
            # If metadata validation fails but the index exists, try with force=True
            if force_reload:
                click.echo("🔄 Force reloading embeddings...")
                return self.embedder.load_vector_store(force=True)
        else:
            click.echo(f"⚠️ No embeddings found at {collection_path}.")
            click.echo("Run 'langdoc parse --use-rag' first to generate embeddings.")
        
        return False


# Create pass_langdoc_ctx decorator similar to click's pass_context
pass_langdoc_ctx = click.make_pass_decorator(LangDocContext, ensure=True)
