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
        """Initialize or reload the embedder."""
        if self.embedder is None or force_reload:
            self.embedder = CodeEmbedder()
        
        # Check if index exists and load it
        index_exists = os.path.exists(os.path.join(self.embedder.FAISS_INDEX_DIR, self.embedder.FAISS_INDEX_NAME + ".faiss"))
        if index_exists and not force_reload:
            return self.embedder.load_vector_store()
        
        return False


# Create pass_langdoc_ctx decorator similar to click's pass_context
pass_langdoc_ctx = click.make_pass_decorator(LangDocContext, ensure=True)
