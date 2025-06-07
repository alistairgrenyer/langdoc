"""
CLI Context module for managing state and dependencies across commands.
Provides centralized access to project information, configuration and RAG functionality.
"""
import logging
import click
from functools import wraps
from typing import Dict, Any, Optional, List

from langdoc.core.embedding import CodeEmbedder
from langdoc.core.services.embedding_service import EmbeddingService
from langdoc.utils.common import load_config, get_config_value, get_project_name
from langdoc.cli.utils import validate_api_key


class LangDocContext:
    """Context object for sharing state and functionality between CLI commands."""
    
    def __init__(self):
        self.embedder: Optional[CodeEmbedder] = None
        self.config: Dict[str, Any] = {}
        self.repo_path: str = ""
        self.file_ext: str = ".py"
        self.skip_dirs: list = []
        self.logger = logging.getLogger("langdoc")
        if not validate_api_key("OPENAI_API_KEY", "Cannot proceed."):
            raise click.ClickException("OPENAI_API_KEY is not set. Please set it in your environment variables.")
    
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
        # Create embedding service
        embedding_service = EmbeddingService(
            repo_path=self.repo_path,
            file_ext=self.file_ext,
            skip_dirs=self.skip_dirs
        )
        
        # Try to load existing embeddings first
        if not force_reload and embedding_service.embeddings_exist():
            if embedding_service.load_existing_embeddings():
                self.logger.info("Successfully loaded existing embeddings")
                self.embedder = embedding_service.embedder
                return True
        
        # No embeddings or forced rebuild - create new ones
        self.logger.info("Creating embeddings - this may take a while...")
        embedder = embedding_service.get_or_create_embeddings(force_rebuild=force_reload)
        if embedder:
            self.embedder = embedder
            return True
        else:
            self.logger.error("Failed to initialize embeddings")
            return False
        
    def get_project_information(self) -> Dict[str, Any]:
        """Get basic project information.
        
        Returns:
            Dict containing project information like name, file structure, etc.
        """
        project_name = get_project_name(self.repo_path)
        return {
            "name": project_name,
            "repo_path": self.repo_path,
            "file_ext": self.file_ext
        }
    
    def get_file_descriptions(self, limit: int = 5) -> List[Dict[str, str]]:
        """Use RAG to retrieve descriptions of important files in the project.
        
        Args:
            limit: Maximum number of files to return descriptions for
            
        Returns:
            List of dictionaries with file path and description
        """
        if not self.embedder or not self.embedder.vector_store:
            self.logger.warning("Cannot retrieve file descriptions: embedder not initialized")
            return []
            
        # List of common patterns for important files
        important_file_patterns = [
            "main", "app", "index", "core", "model", 
            "util", "config", "client", "server"
        ]
        
        found_files = []
        
        # Search for important files using RAG
        for pattern in important_file_patterns:
            if len(found_files) >= limit:
                break
                
            query = f"file:{pattern} type:function"
            try:
                results = self.embedder.similarity_search(query, k=3)
                for doc in results:
                    filepath = doc.metadata.get('filepath', '')
                    if filepath and filepath not in [f['file'] for f in found_files]:
                        found_files.append({
                            'file': filepath,
                            'content': doc.page_content
                        })
            except Exception as e:
                self.logger.warning(f"Error retrieving file information for pattern '{pattern}': {e}")
        
        return found_files


# Configure logging
def configure_logging(level=logging.INFO):
    """Configure logging for the application."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Create context-passing decorator for Click commands
def pass_langdoc_ctx(f):
    """Decorator to pass LangDocContext to Click commands with better error handling."""
    @wraps(f)
    @click.make_pass_decorator(LangDocContext, ensure=True)
    def new_func(ctx, *args, **kwargs):
        try:
            return f(ctx, *args, **kwargs)
        except Exception as e:
            ctx.logger.exception(f"Command failed: {e}")
            click.echo(f"Error: {e}", err=True)
            # Exit with error code
            ctx.exit(1)
            
    return new_func
