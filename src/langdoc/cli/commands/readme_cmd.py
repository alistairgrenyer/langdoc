"""
README generation command implementation for langdoc CLI.
"""
import os
import sys
import click
import logging

from langdoc.cli.utils import echo_styled
from langdoc.cli.context import pass_langdoc_ctx, LangDocContext, configure_logging
from langdoc.core.services.readme_service import ReadmeService
from langdoc.core.services.embedding_service import EmbeddingService


@click.command()
@click.option('--path', 'repo_path', default='.', 
              help='Path to the Git repository.', 
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), 
              show_default=True)
@click.option('--output-file', default='README.md', 
              help='File to save the generated README.', 
              type=click.Path(dir_okay=False, writable=True), 
              show_default=True)
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--force-rebuild', is_flag=True, help='Force rebuild embeddings even if they exist')
@pass_langdoc_ctx
def readme(ctx: LangDocContext, repo_path: str, output_file: str, verbose: bool, force_rebuild: bool):
    """Generate or update the README.md file using RAG.
    
    Automatically creates embeddings if they don't exist or if force-rebuild is specified.
    """
    # Configure logging based on verbosity
    log_level = logging.DEBUG if verbose else logging.INFO
    configure_logging(log_level)
    logger = logging.getLogger("langdoc.cli.readme")
    
    echo_styled(f"--- Generating README for: {os.path.abspath(repo_path)} ---", "header")

    # Initialize context with repository path
    try:
        ctx.init_from_repo_path(repo_path)
    except Exception as e:
        echo_styled(f"Error initializing context: {e}", "error")
        sys.exit(1)
    
    # Initialize README service with model from config
    model_name = ctx.config.get('llm_model', 'gpt-3.5-turbo')
    echo_styled("Initializing README generator...", "info")
    readme_service = ReadmeService(model_name=model_name)

    # Create embeddings service
    embedding_service = EmbeddingService(
        repo_path=repo_path,
        file_ext=ctx.file_ext,
        skip_dirs=ctx.skip_dirs
    )
    
    # Check for existing embeddings
    if not embedding_service.embeddings_exist() or force_rebuild:
        echo_styled("Embeddings not found or force rebuild requested", "info")
        echo_styled("Creating embeddings - this may take a while...", "info")
        
        success, embedder = embedding_service.create_embeddings(force_rebuild=force_rebuild)
        if success and embedder:
            ctx.embedder = embedder
            echo_styled("✅ Embeddings created successfully", "success")
        else:
            echo_styled("❌ Failed to create embeddings", "error")
            echo_styled("Cannot generate README without embeddings", "error")
            sys.exit(1)
    else:
        # Load existing embeddings
        echo_styled("Loading existing embeddings", "info")
        if embedding_service.load_existing_embeddings():
            ctx.embedder = embedding_service.embedder
            echo_styled("✅ Embeddings loaded successfully", "success")
        else:
            echo_styled("❌ Failed to load embeddings", "error")
            sys.exit(1)
    
    # Get project information
    echo_styled("Gathering project information...", "info")
    project_info = ctx.get_project_information()
    
    # Get file descriptions using RAG
    echo_styled("Using RAG to retrieve file descriptions...", "info")
    try:
        # Now that we have embeddings, get file descriptions
        file_data = ctx.get_file_descriptions(limit=5)
        
        if not file_data:
            echo_styled("Warning: No file data could be retrieved using RAG", "warning")
    except Exception as e:
        logger.exception("Error retrieving file descriptions")
        echo_styled(f"Error retrieving file descriptions: {e}", "warning")
        file_data = []
    
    # Generate README content
    echo_styled("Generating README content...", "info")
    try:
        readme_content = readme_service.generate_readme(
            project_info=project_info,
            file_data=file_data,
            repo_path=repo_path,
            skip_dirs=ctx.skip_dirs
        )
    except Exception as e:
        logger.exception("Error generating README content")
        echo_styled(f"Error generating README: {e}", "error")
        sys.exit(1)
    
    # Save README to file
    output_path = os.path.join(repo_path, output_file)
    echo_styled(f"Saving README to {output_path}", "info")
    
    if readme_service.save_readme(readme_content, output_path):
        echo_styled(f"README successfully generated at {output_path}", "success")
    else:
        echo_styled(f"Failed to save README to {output_path}", "error")
        sys.exit(1)
