"""
Parse command implementation for langdoc CLI.
"""
import os
import click

from embedding import CodeEmbedder
from cli.context import pass_langdoc_ctx, LangDocContext
from cli.utils import echo_styled, get_parsed_files, validate_api_key


@click.command()
@click.option('--path', 'repo_path', default='.', 
              help='Path to the Git repository.', 
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), 
              show_default=True)
@click.option('--force-rebuild', is_flag=True, 
              help='Force rebuild of the vector store even if one exists.')
@pass_langdoc_ctx
def parse(ctx: LangDocContext, repo_path: str, force_rebuild: bool):
    """Parse the repository, build and save embeddings."""
    echo_styled(f"--- Starting Parse & Embed for: {os.path.abspath(repo_path)} ---", "header")

    # Validate API key - will exit if not present
    validate_api_key("OPENAI_API_KEY", "Cannot proceed with embedding.")

    # Initialize context with repository path
    ctx.init_from_repo_path(repo_path)
    
    # Initialize embedder with repository path for proper metadata tracking
    embedder = CodeEmbedder(repo_path=repo_path)
    
    # Check if Chroma database exists for this repository
    db_path = os.path.join(repo_path, embedder.DB_DIR)
    collection_name = embedder._collection_name
    collection_path = os.path.join(db_path, collection_name)
    db_exists = os.path.exists(collection_path) and os.path.exists(os.path.join(collection_path, "chroma.sqlite3"))

    if db_exists and not force_rebuild:
        echo_styled("✅ Chroma database already exists. Loading it.", "success")
        if embedder.load_vector_store():
            echo_styled("Successfully loaded existing vector store.", "success")
            ctx.embedder = embedder
            echo_styled("To re-parse and rebuild the embeddings, use the --force-rebuild flag.")
            return
        else:
            echo_styled("⚠️ Failed to load existing database. Will rebuild.", "warning")
    elif force_rebuild and db_exists:
        echo_styled("🔄 Force rebuild requested. Clearing existing embeddings...", "info")
        # Clear existing embeddings
        CodeEmbedder.clear_embeddings(repo_path)
    
    # Parse files
    parsed_files = get_parsed_files(repo_path, ctx.file_ext, ctx.skip_dirs)
    if not parsed_files:
        echo_styled("No files parsed. Aborting embedding.", "warning")
        return

    echo_styled(f"Creating LangChain documents from {len(parsed_files)} parsed files...", "info")
    documents_to_embed = embedder.create_documents_from_parsed_data(parsed_files)

    if not documents_to_embed:
        echo_styled("No documents created for embedding. Check parsing results.", "warning")
        return

    echo_styled(f"Building vector store with {len(documents_to_embed)} documents...", "info")
    if embedder.build_vector_store(documents_to_embed):
        echo_styled("✅ Vector store built and persisted successfully.", "success")
        # Vector store is automatically persisted by Chroma, but we'll save metadata explicitly
        embedder.save_vector_store()
        ctx.embedder = embedder
        
        # Display database location
        echo_styled(f"Embeddings saved to: {collection_path}", "info")
        echo_styled("You can now use 'langdoc ask' and 'langdoc readme --use-rag' with these embeddings.", "info")
    else:
        echo_styled("❌ Failed to build vector store.", "error")
