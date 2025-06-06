import click
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from parser import get_file_paths, parse_python_file
from embedding import CodeEmbedder, OPENAI_API_KEY as EMBED_OPENAI_API_KEY
from docgen import DocGenerator, OPENAI_API_KEY as DOCGEN_OPENAI_API_KEY
from utils import load_config, get_config_value, get_project_name, get_file_tree

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# Load .env file at the beginning
load_dotenv()

# Global state for embedder (can be initialized by 'parse' and used by 'ask')
# This is a simple way; for more complex apps, consider a context object or dependency injection.
global_embedder: CodeEmbedder = None

@click.group()
@click.pass_context
def cli(ctx):
    """LangDoc: A CLI tool to analyze and document Git repositories using LangChain and RAG."""
    ctx.ensure_object(dict)
    # Load config once and pass it around if needed, or load per command
    # For simplicity, we'll load config within commands that need it.
    pass

def get_common_options(repo_path: str) -> Dict[str, Any]:
    config = load_config(repo_path)
    file_ext = get_config_value(config, 'file_ext', '.py')
    skip_dirs_str = get_config_value(config, 'skip_dirs', 'tests,.git,.venv,__pycache__,node_modules,.vscode,.idea,dist,build,docs')
    skip_dirs_list = [d.strip() for d in skip_dirs_str.split(',') if d.strip()]
    return {"file_ext": file_ext, "skip_dirs": skip_dirs_list, "config": config}

def _get_parsed_files(repo_path: str, file_ext: str, skip_dirs: List[str]) -> List[Dict[str, Any]]:
    click.echo(f"Scanning for {file_ext} files in '{repo_path}', skipping {skip_dirs}...")
    file_paths = get_file_paths(repo_path, file_ext, skip_dirs)
    if not file_paths:
        click.echo(click.style(f"No {file_ext} files found in '{repo_path}' (after skipping specified directories).", fg='yellow'))
        return []
    
    click.echo(f"Found {len(file_paths)} {file_ext} files to parse.")
    
    parsed_files_data = []
    with click.progressbar(file_paths, label='Parsing files') as bar:
        for f_path in bar:
            # click.echo(f"Parsing {f_path}...")
            parsed_data = parse_python_file(f_path)
            if "error" in parsed_data:
                click.echo(click.style(f"Error parsing {f_path}: {parsed_data['error']}", fg='red'))
            elif parsed_data.get('definitions'): # Only add files that have some definitions
                parsed_files_data.append(parsed_data)
            # else:
                # click.echo(click.style(f"No definitions found in {f_path}, skipping for embedding/docgen.", fg='yellow'))
    return parsed_files_data

@cli.command()
@click.option('--path', 'repo_path', default='.', help='Path to the Git repository.', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), show_default=True)
@click.option('--force-rebuild', is_flag=True, help='Force rebuild of the vector store even if one exists.')
def parse(repo_path: str, force_rebuild: bool):
    """Parse the repository, build and save embeddings."""
    global global_embedder
    click.echo(click.style(f"--- Starting Parse & Embed for: {os.path.abspath(repo_path)} ---", bold=True))

    if not EMBED_OPENAI_API_KEY:
        click.echo(click.style("OPENAI_API_KEY not found. Cannot proceed with embedding.", fg='red'))
        return

    common_opts = get_common_options(repo_path)
    file_ext = common_opts['file_ext']
    skip_dirs = common_opts['skip_dirs']

    embedder = CodeEmbedder()
    index_exists = os.path.exists(os.path.join(embedder.FAISS_INDEX_DIR, embedder.FAISS_INDEX_NAME + ".faiss"))

    if index_exists and not force_rebuild:
        click.echo(click.style("FAISS index already exists. Loading it.", fg='green'))
        if embedder.load_vector_store():
            click.echo(click.style("Successfully loaded existing vector store.", fg='green'))
            global_embedder = embedder # Update global embedder
            click.echo("To re-parse and rebuild the index, use the --force-rebuild flag.")
            return
        else:
            click.echo(click.style("Failed to load existing index. Will attempt to rebuild.", fg='yellow'))
    
    parsed_files = _get_parsed_files(repo_path, file_ext, skip_dirs)
    if not parsed_files:
        click.echo(click.style("No files parsed. Aborting embedding.", fg='yellow'))
        return

    click.echo(f"Creating LangChain documents from {len(parsed_files)} parsed files...")
    documents_to_embed = embedder.create_documents_from_parsed_data(parsed_files)

    if not documents_to_embed:
        click.echo(click.style("No documents created for embedding. Check parsing results.", fg='yellow'))
        return

    click.echo(f"Building vector store with {len(documents_to_embed)} documents...")
    embedder.build_vector_store(documents_to_embed)

    if embedder.vector_store:
        click.echo(click.style("Vector store built successfully.", fg='green'))
        embedder.save_vector_store()
        global_embedder = embedder # Update global embedder
    else:
        click.echo(click.style("Failed to build vector store.", fg='red'))

@cli.command()
@click.option('--path', 'repo_path', default='.', help='Path to the Git repository.', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), show_default=True)
@click.option('--output-dir', default='docs', help='Directory to save generated documentation.', type=click.Path(file_okay=False, writable=True), show_default=True)
@click.option('--update-docstrings', is_flag=True, help='Attempt to update docstrings in source files (currently prints suggestions).')
def doc(repo_path: str, output_dir: str, update_docstrings: bool):
    """Generate code comments and markdown documentation."""
    click.echo(click.style(f"--- Starting Documentation Generation for: {os.path.abspath(repo_path)} ---", bold=True))

    if not DOCGEN_OPENAI_API_KEY:
        click.echo(click.style("OPENAI_API_KEY not found. LLM-based documentation features will be limited.", fg='yellow'))
        # Allow to proceed if only parsing and basic summarization is needed, but LLM calls will fail.

    common_opts = get_common_options(repo_path)
    file_ext = common_opts['file_ext']
    skip_dirs = common_opts['skip_dirs']
    config = common_opts['config']
    llm_model = get_config_value(config, 'llm_model', 'gpt-3.5-turbo')

    doc_generator = DocGenerator(model_name=llm_model)

    parsed_files = _get_parsed_files(repo_path, file_ext, skip_dirs)
    if not parsed_files:
        click.echo(click.style("No files parsed. Aborting documentation generation.", fg='yellow'))
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        click.echo(f"Created output directory: {output_dir}")

    click.echo(f"Generating markdown documentation for {len(parsed_files)} files into '{output_dir}'...")
    generated_md_files = []
    with click.progressbar(parsed_files, label='Generating module docs') as bar:
        for pf_data in bar:
            if update_docstrings:
                if DOCGEN_OPENAI_API_KEY:
                    click.echo(f"Checking/Updating docstrings for {pf_data['file_path']}...")
                    # This currently prints suggestions, actual file modification is complex
                    doc_generator.update_file_with_docstrings(pf_data['file_path'], pf_data)
                else:
                    click.echo(click.style(f"Skipping docstring update for {pf_data['file_path']} (OPENAI_API_KEY missing).", fg='yellow'))
            
            md_file_path = doc_generator.generate_module_markdown(pf_data, output_dir=output_dir)
            if md_file_path:
                generated_md_files.append(md_file_path)
    
    if generated_md_files:
        click.echo(click.style(f"Successfully generated {len(generated_md_files)} markdown files in '{output_dir}'.", fg='green'))
    else:
        click.echo(click.style("No markdown files were generated.", fg='yellow'))

@cli.command()
@click.option('--path', 'repo_path', default='.', help='Path to the Git repository.', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), show_default=True)
@click.option('--output-file', default='README.md', help='File to save the generated README.', type=click.Path(dir_okay=False, writable=True), show_default=True)
def readme(repo_path: str, output_file: str):
    """Generate or update the README.md file."""
    click.echo(click.style(f"--- Generating README for: {os.path.abspath(repo_path)} ---", bold=True))

    if not DOCGEN_OPENAI_API_KEY:
        click.echo(click.style("OPENAI_API_KEY not found. README generation will be basic.", fg='yellow'))

    common_opts = get_common_options(repo_path)
    config = common_opts['config']
    file_ext = common_opts['file_ext'] # For file tree and key elements
    skip_dirs = common_opts['skip_dirs']
    llm_model = get_config_value(config, 'llm_model', 'gpt-3.5-turbo')

    doc_generator = DocGenerator(model_name=llm_model)
    project_name = get_project_name(repo_path)

    click.echo("Gathering project information...")
    file_structure_md = get_file_tree(repo_path, skip_dirs=skip_dirs, file_ext_filter=file_ext, max_depth=3)
    
    # For key elements, parse a small number of files or use a heuristic
    # Here, we'll just list some parsed elements if available, or keep it simple
    parsed_files_for_readme = _get_parsed_files(repo_path, file_ext, skip_dirs) # Potentially re-parsing, could optimize
    key_elements_summary_parts = []
    if parsed_files_for_readme:
        for pf_data in parsed_files_for_readme[:5]: # Limit for brevity in README
            for definition in pf_data.get('definitions', [])[:3]: # Limit definitions per file
                key_elements_summary_parts.append(f"- `{definition['name']}` ({definition['type']}) in `{os.path.basename(pf_data['file_path'])}`")
    key_elements_summary = "\n".join(key_elements_summary_parts) if key_elements_summary_parts else "No key elements automatically extracted."

    readme_content = f"# {project_name}\n\n"
    
    # Project Summary Section
    click.echo("Generating Project Summary section...")
    summary_section_content = "A tool to analyze and document Git repositories using LangChain and RAG." # Default/placeholder
    if DOCGEN_OPENAI_API_KEY:
        generated_summary = doc_generator.generate_readme_section(
            section_title="Project Summary",
            project_name=project_name,
            file_structure=file_structure_md,
            key_elements_summary=key_elements_summary
        )
        if generated_summary and generated_summary.lower().strip() != 'no change needed':
            summary_section_content = generated_summary
    readme_content += f"## Project Summary\n{summary_section_content}\n\n"

    # File Structure Section
    readme_content += f"## File Structure\n\n```\n{file_structure_md}\n```\n\n"

    # Key Classes/Functions Section
    readme_content += f"## Notable Classes/Functions\n\n{key_elements_summary}\n\n"

    # Setup Instructions Section
    click.echo("Generating Setup Instructions section...")
    setup_instructions = f"""### Setup

1.  Clone the repository:
    ```bash
    git clone <your-repo-url>
    cd {project_name}
    ```
"""
    has_requirements = os.path.exists(os.path.join(repo_path, 'requirements.txt'))
    has_pyproject = os.path.exists(os.path.join(repo_path, 'pyproject.toml'))

    if has_requirements:
        setup_instructions += """\n
2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\\Scripts\\activate
    pip install -r requirements.txt
    ```
"""
    elif has_pyproject:
        setup_instructions += """\n
2.  This project uses Poetry (or similar). Install dependencies:
    ```bash
    poetry install
    ```
""" 
        # Add other common pyproject.toml based setups if needed
    else:
        setup_instructions += "\n2. Install dependencies (manual step - check project for details).\n"
    
    if os.path.exists(os.path.join(repo_path, '.env.example')):
        setup_instructions += "\n3. Set up environment variables:\n   Copy `.env.example` to `.env` and fill in your API keys (e.g., `OPENAI_API_KEY`).\n   ```bash\n   cp .env.example .env\n   ```\n"

    readme_content += f"## Setup and Usage\n\n{setup_instructions}\n"
    readme_content += """### Running LangDoc Commands

Once setup, you can use the LangDoc CLI:

-   **Parse the repository and build embeddings:**
    ```bash
    python cli.py parse --path /path/to/your/repo
    ```
-   **Generate documentation:**
    ```bash
    python cli.py doc --path /path/to/your/repo --output-dir project_docs
    ```
-   **Ask questions about the code:**
    ```bash
    python cli.py ask "How does the authentication work?" --path /path/to/your/repo
    ```
-   **Refresh this README:**
    ```bash
    python cli.py readme --path /path/to/your/repo
    ```
"""

    try:
        with open(os.path.join(repo_path, output_file), 'w', encoding='utf-8') as f:
            f.write(readme_content)
        click.echo(click.style(f"README generated/updated at {os.path.join(repo_path, output_file)}", fg='green'))
    except IOError as e:
        click.echo(click.style(f"Error writing README to {os.path.join(repo_path, output_file)}: {e}", fg='red'))

@cli.command()
@click.argument('question')
@click.option('--path', 'repo_path', default='.', help='Path to the Git repository where embeddings were built.', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), show_default=True)
def ask(question: str, repo_path: str):
    """Ask high-level questions about the project using RAG."""
    global global_embedder
    click.echo(click.style(f"--- Asking Question about: {os.path.abspath(repo_path)} ---", bold=True))
    click.echo(f"Question: {question}")

    if not EMBED_OPENAI_API_KEY or not DOCGEN_OPENAI_API_KEY: # RAG needs both for embeddings and generation
        click.echo(click.style("OPENAI_API_KEY not found. Cannot proceed with 'ask' command.", fg='red'))
        return

    config = load_config(repo_path)
    llm_model = get_config_value(config, 'llm_model', 'gpt-3.5-turbo') # Or a more powerful one for RAG

    if global_embedder is None or global_embedder.vector_store is None:
        click.echo("Embedder not initialized or vector store not loaded. Attempting to load...")
        embedder_instance = CodeEmbedder()
        if embedder_instance.load_vector_store(path=os.path.join(repo_path, CodeEmbedder.FAISS_INDEX_DIR)):
            global_embedder = embedder_instance
            click.echo(click.style("Vector store loaded successfully.", fg='green'))
        else:
            click.echo(click.style("Failed to load vector store. Please run 'parse' command first on this repository.", fg='red'))
            return
    
    if global_embedder.vector_store is None:
         click.echo(click.style("Vector store is not available even after attempting load. Please run 'parse'.", fg='red'))
         return

    click.echo("Performing similarity search for relevant code context...")
    try:
        retrieved_docs = global_embedder.similarity_search(question, k=5) # Get top 5 relevant chunks
    except Exception as e:
        click.echo(click.style(f"Error during similarity search: {e}", fg='red'))
        return

    if not retrieved_docs:
        click.echo(click.style("No relevant code snippets found for your question.", fg='yellow'))
        return

    click.echo(f"Found {len(retrieved_docs)} relevant document(s). Synthesizing answer...")
    # for i, doc_item in enumerate(retrieved_docs):
    #     click.echo(f"  Snippet {i+1} from: {doc_item.metadata.get('source')} ({doc_item.metadata.get('name')})")

    # Setup RAG chain
    llm = ChatOpenAI(model=llm_model, temperature=0.3, openai_api_key=DOCGEN_OPENAI_API_KEY)
    
    # Basic RAG prompt
    # You can enhance this prompt significantly for better results
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

    # Create a chain that combines the documents into a single string (stuffing)
    # and then passes it to the LLM with the prompt.
    document_chain = create_stuff_documents_chain(llm, rag_prompt)
    
    # Create the retrieval chain
    # This chain takes a user's question, uses the retriever to fetch relevant documents,
    # then passes those documents and the original question to the LLM to generate an answer.
    # We are using a pre-loaded retriever (global_embedder.vector_store.as_retriever())
    retriever = global_embedder.vector_store.as_retriever(search_kwargs={"k": 5})
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    try:
        response = retrieval_chain.invoke({"input": question})
        answer = response.get('answer', "Sorry, I couldn't formulate an answer based on the retrieved context.")
        click.echo(click.style("\nAnswer:", bold=True)) 
        click.echo(answer)

        # Optionally, show sources if you want to trace back
        # click.echo(click.style("\nSources considered:", bold=True))
        # for i, doc_item in enumerate(response.get('context', [])):
        #     click.echo(f"  {i+1}. {doc_item.metadata.get('source')} - {doc_item.metadata.get('name')}")

    except Exception as e:
        click.echo(click.style(f"Error during RAG chain invocation: {e}", fg='red'))

if __name__ == '__main__':
    cli(obj={})
