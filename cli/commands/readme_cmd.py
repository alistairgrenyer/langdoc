"""
README generation command implementation for langdoc CLI.
"""
import os
import click

from docgen import DocGenerator
from embedding import CodeEmbedder
from utils import get_config_value, get_project_name, get_file_tree
from cli.context import pass_langdoc_ctx, LangDocContext
from cli.utils import echo_styled, get_parsed_files, validate_api_key


@click.command()
@click.option('--path', 'repo_path', default='.', 
              help='Path to the Git repository.', 
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), 
              show_default=True)
@click.option('--output-file', default='README.md', 
              help='File to save the generated README.', 
              type=click.Path(dir_okay=False, writable=True), 
              show_default=True)
@click.option('--use-rag', is_flag=True, 
              help='Use RAG to enhance documentation with detailed file and function descriptions.')
@pass_langdoc_ctx
def readme(ctx: LangDocContext, repo_path: str, output_file: str, use_rag: bool):
    """Generate or update the README.md file."""
    echo_styled(f"--- Generating README for: {os.path.abspath(repo_path)} ---", "header")

    # Validate API key - will exit if not present
    validate_api_key("OPENAI_API_KEY", "Cannot proceed with README generation.")

    # Initialize context with repository path
    ctx.init_from_repo_path(repo_path)
    
    # Initialize doc generator
    llm_model = get_config_value(ctx.config, 'llm_model', 'gpt-3.5-turbo')
    doc_generator = DocGenerator(model_name=llm_model)
    project_name = get_project_name(repo_path)

    echo_styled("Gathering project information...", "info")
    file_structure_md = get_file_tree(repo_path, skip_dirs=ctx.skip_dirs, file_ext_filter=ctx.file_ext, max_depth=3)
    
    # For key elements, parse some files to extract information
    parsed_files_for_readme = get_parsed_files(repo_path, ctx.file_ext, ctx.skip_dirs)
    key_elements_summary_parts = []
    if parsed_files_for_readme:
        for pf_data in parsed_files_for_readme[:5]:  # Limit for brevity in README
            for definition in pf_data.get('definitions', [])[:3]:  # Limit definitions per file
                key_elements_summary_parts.append(
                    f"- `{definition['name']}` ({definition['type']}) in `{os.path.basename(pf_data['file_path'])}`"
                )
    key_elements_summary = "\n".join(key_elements_summary_parts) if key_elements_summary_parts else "No key elements automatically extracted."

    # Get detailed file descriptions using RAG if requested
    file_descriptions = "No detailed file descriptions available."
    
    if use_rag:
        echo_styled("Using RAG to retrieve detailed file descriptions...", "info")
        try:
            # Initialize embedder if not already done
            if ctx.embedder is None:
                ctx.init_embedder()
            
            # If embedder still not initialized, try to create it
            if ctx.embedder is None or ctx.embedder.vector_store is None:
                echo_styled("Building embeddings for RAG...", "info")
                embedder = CodeEmbedder(model_name=get_config_value(ctx.config, 'embed_model', 'text-embedding-ada-002'))
                # Use the parsed files we already have to create documents
                documents_to_embed = []
                if parsed_files_for_readme:
                    documents_to_embed = embedder.create_documents_from_parsed_data(parsed_files_for_readme)
                    if documents_to_embed:
                        echo_styled(f"Building vector store with {len(documents_to_embed)} documents...", "info")
                        embedder.build_vector_store(documents_to_embed)
                        ctx.embedder = embedder
            
            if ctx.embedder and ctx.embedder.vector_store:
                # Generate queries for key files to get detailed descriptions
                file_desc_parts = []
                for file_path in [f['file_path'] for f in parsed_files_for_readme]:
                    file_name = os.path.basename(file_path)
                    query = f"What is the purpose and main functionality of {file_name}?"
                    docs = ctx.embedder.vector_store.similarity_search(query, k=3)
                    if docs:
                        content_summary = " ".join([doc.page_content for doc in docs[:2]])
                        file_desc_parts.append(f"### {file_name}\n{content_summary[:500]}...")
                
                if file_desc_parts:
                    file_descriptions = "\n\n".join(file_desc_parts)
                    echo_styled(f"Retrieved detailed descriptions for {len(file_desc_parts)} files using RAG", "success")
        except Exception as e:
            echo_styled(f"Error using RAG for file descriptions: {e}", "warning")
            echo_styled("Falling back to basic README generation...", "info")
    # No else clause needed as validate_api_key would have exited if key not present

    # Start building the README content
    readme_content = f"# {project_name}\n\n"
    
    # Project Summary Section
    echo_styled("Generating Project Summary section...", "info")
    summary_section_content = "A tool to analyze and document Git repositories using LangChain and RAG."  # Default
    # Always use LLM since we enforce API key
    summary_section_content = doc_generator.generate_readme_section(
        section_title="Project Summary",
        project_name=project_name,
        file_structure=file_structure_md,
        key_elements_summary=key_elements_summary,
        file_descriptions=file_descriptions
    )
    if summary_section_content and summary_section_content.lower().strip() != 'no change needed':
        # Let the LLM handle the heading
        readme_content += f"{summary_section_content}\n\n"
    else:
        # Fallback with added heading
        readme_content += "## Project Summary\nA tool to analyze and document Git repositories using LangChain and RAG.\n\n"


    # File Structure Section
    echo_styled("Generating File Structure section...", "info")
    # Always use LLM since we enforce API key
    file_structure_content = doc_generator.generate_readme_section(
        section_title="File Structure",
        project_name=project_name,
        file_structure=file_structure_md,
        key_elements_summary=key_elements_summary,
        file_descriptions=file_descriptions
    )
    if file_structure_content and file_structure_content.lower().strip() != 'no change needed':
        # Let the LLM handle the heading
        readme_content += f"{file_structure_content}\n\n"
    else:
        # Fallback with added heading
        readme_content += f"## File Structure\n\n```\n{file_structure_md}\n```\n\n"


    # Key Classes/Functions Section
    echo_styled("Generating Notable Classes/Functions section...", "info")
    # Always use LLM since we enforce API key
    notable_elements_content = doc_generator.generate_readme_section(
        section_title="Notable Classes/Functions",
        project_name=project_name,
        file_structure=file_structure_md,
        key_elements_summary=key_elements_summary,
        file_descriptions=file_descriptions
    )
    if notable_elements_content and notable_elements_content.lower().strip() != 'no change needed':
        # Let the LLM handle the heading
        readme_content += f"{notable_elements_content}\n\n"
    else:
        # Fallback with added heading
        readme_content += f"## Notable Classes/Functions\n\n{key_elements_summary}\n\n"


    # Setup Instructions Section
    echo_styled("Generating Setup Instructions section...", "info")
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
        echo_styled(f"README generated/updated at {os.path.join(repo_path, output_file)}", "success")
    except IOError as e:
        echo_styled(f"Error writing README to {os.path.join(repo_path, output_file)}: {e}", "error")
