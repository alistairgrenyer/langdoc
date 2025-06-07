"""
Ask command implementation for langdoc CLI.
"""
import os
import click

from langdoc.core.embedding import CodeEmbedder
from langdoc.cli.context import pass_langdoc_ctx, LangDocContext
from langdoc.cli.utils import echo_styled, validate_api_key
from langdoc.core.generators.ask import AskGenerator

@click.command()
@click.argument('question')
@click.option('--path', 'repo_path', default='.', 
              help='Path to the Git repository where embeddings were built.', 
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), 
              show_default=True)
@pass_langdoc_ctx
def ask(ctx: LangDocContext, question: str, repo_path: str):
    """Ask high-level questions about the project using RAG."""
    echo_styled(f"--- Asking Question about: {os.path.abspath(repo_path)} ---", "header")
    echo_styled(f"Question: {question}", "info")

    # Validate API key - will exit if not present
    validate_api_key("OPENAI_API_KEY", "Cannot proceed with RAG query.")

    # Initialize context with repository path
    ctx.init_from_repo_path(repo_path)
    
    # Get LLM model from config
    llm_model = ctx.config.get('llm_model', 'gpt-3.5-turbo')

    # Initialize embedder if needed
    if ctx.embedder is None:
        echo_styled("Embedder not initialized. Attempting to load...", "info")
        ctx.init_embedder()
    
    # If still not initialized, try to load vector store directly
    if ctx.embedder is None or ctx.embedder.vector_store is None:
        echo_styled("Trying to load vector store from disk...", "info")
        # Initialize CodeEmbedder with repository path for proper metadata tracking
        embedder = CodeEmbedder(repo_path=repo_path)
        
        # Try loading with repository metadata validation
        if embedder.load_vector_store():
            ctx.embedder = embedder
            echo_styled("✅ Vector store loaded successfully.", "success")
        else:
            # Try again with force=True as a fallback if it failed due to metadata mismatch
            echo_styled("Attempting to load vector store without metadata validation...", "info")
            if embedder.load_vector_store(force=True):
                ctx.embedder = embedder
                echo_styled("⚠️ Vector store loaded with force option.", "warning")
                echo_styled("Note: It may not match the current repository state.", "warning")
                echo_styled("Consider running 'parse' or 'readme --use-rag' to update embeddings.", "info")
            else:
                echo_styled("❌ Failed to load vector store.", "error")
                echo_styled("Please run 'parse' or 'readme --use-rag' command first on this repository.", "error")
                return
    
    # Double-check that we have a working embedder with vector store
    if ctx.embedder.vector_store is None:
        echo_styled("Vector store is not available even after attempting load. Please run 'parse'.", "error")
        return

    # Perform similarity search to find relevant documents
    echo_styled("Performing similarity search for relevant code context...", "info")
    try:
        retrieved_docs = ctx.embedder.similarity_search(question, k=5)  # Get top 5 relevant chunks
    except Exception as e:
        echo_styled(f"Error during similarity search: {e}", "error")
        return

    if not retrieved_docs:
        echo_styled("No relevant code snippets found for your question.", "warning")
        return

    echo_styled(f"Found {len(retrieved_docs)} relevant document(s). Synthesizing answer...", "info")

    # Initialize the AskGenerator
    ask_generator = AskGenerator(model_name=llm_model)
    
    # Create retriever from the vector store
    retriever = ctx.embedder.vector_store.as_retriever(search_kwargs={"k": 5})
    
    # Execute the generator to get an answer
    try:
        # Use the generator to get an answer
        response = ask_generator.generate_answer(question, retriever)
        answer = response.get('answer', "Sorry, I couldn't formulate an answer based on the retrieved context.")
        echo_styled("\nAnswer:", "header")
        echo_styled(answer, "default")

        # Optionally, you could add a flag to show sources
        # echo_styled("\nSources considered:", "header")
        # for i, doc_item in enumerate(response.get('context', [])):
        #     echo_styled(f"  {i+1}. {doc_item.metadata.get('source')} - {doc_item.metadata.get('name')}", "info")
    except Exception as e:
        echo_styled(f"Error during answer generation: {e}", "error")
