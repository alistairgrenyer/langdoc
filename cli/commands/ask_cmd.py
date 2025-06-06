"""
Ask command implementation for langdoc CLI.
"""
import os
import click

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from embedding import CodeEmbedder
from utils import get_config_value
from cli.context import pass_langdoc_ctx, LangDocContext
from cli.utils import echo_styled, validate_api_key


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
    llm_model = get_config_value(ctx.config, 'llm_model', 'gpt-3.5-turbo')

    # Initialize embedder if needed
    if ctx.embedder is None:
        echo_styled("Embedder not initialized. Attempting to load...", "info")
        ctx.init_embedder()
    
    # If still not initialized, try to load vector store directly
    if ctx.embedder is None or ctx.embedder.vector_store is None:
        echo_styled("Trying to load vector store from disk...", "info")
        embedder = CodeEmbedder()
        if embedder.load_vector_store(path=os.path.join(repo_path, CodeEmbedder.FAISS_INDEX_DIR)):
            ctx.embedder = embedder
            echo_styled("Vector store loaded successfully.", "success")
        else:
            echo_styled("Failed to load vector store. Please run 'parse' command first on this repository.", "error")
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

    # Setup RAG chain
    llm = ChatOpenAI(model=llm_model, temperature=0.3)
    
    # RAG prompt
    rag_prompt_template = """
    You are an AI assistant helping to answer questions about a codebase.
    Use the following retrieved code context to answer the question.
    If you don't know the answer from the context, say that you don't know.
    Be concise and focus on the information present in the provided context.

    Context:
    {context}

    Question: {input}

    Answer:
    """
    rag_prompt = ChatPromptTemplate.from_template(rag_prompt_template)

    # Create the document chain for combining documents into context
    document_chain = create_stuff_documents_chain(llm, rag_prompt)
    
    # Create the retrieval chain with the vector store as retriever
    retriever = ctx.embedder.vector_store.as_retriever(search_kwargs={"k": 5})
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    # Execute the chain and display results
    try:
        response = retrieval_chain.invoke({"input": question})
        answer = response.get('answer', "Sorry, I couldn't formulate an answer based on the retrieved context.")
        echo_styled("\nAnswer:", "header")
        echo_styled(answer, "default")

        # Optionally, you could add a flag to show sources
        # echo_styled("\nSources considered:", "header")
        # for i, doc_item in enumerate(response.get('context', [])):
        #     echo_styled(f"  {i+1}. {doc_item.metadata.get('source')} - {doc_item.metadata.get('name')}", "info")
    except Exception as e:
        echo_styled(f"Error during RAG chain invocation: {e}", "error")
