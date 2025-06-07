"""
README generation command implementation for langdoc CLI.
"""
import os
import click
from langdoc.cli.utils import echo_styled, get_parsed_files, validate_api_key
from langdoc.utils.common import get_project_name, get_file_tree
from langdoc.core.generators.readme import ReadmeGenerator
from langdoc.core.embedding import CodeEmbedder
from langdoc.cli.context import pass_langdoc_ctx, LangDocContext


@click.command()
@click.option('--path', 'repo_path', default='.', 
              help='Path to the Git repository.', 
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), 
              show_default=True)
@click.option('--output-file', default='README.md', 
              help='File to save the generated README.', 
              type=click.Path(dir_okay=False, writable=True), 
              show_default=True)
@pass_langdoc_ctx
def readme(ctx: LangDocContext, repo_path: str, output_file: str):
    """Generate or update the README.md file."""
    echo_styled(f"--- Generating README for: {os.path.abspath(repo_path)} ---", "header")

    # Validate API key - will exit if not present
    validate_api_key("OPENAI_API_KEY", "Cannot proceed with README generation.")

    # Initialize context with repository path
    ctx.init_from_repo_path(repo_path)
    
    # Initialize doc generator
    model_name = ctx.config.get('llm_model', 'gpt-3.5-turbo')
    echo_styled("Initializing README generator...", "info")
    readme_generator = ReadmeGenerator(model_name=model_name)
    project_name = get_project_name(repo_path)

    echo_styled("Gathering project information...", "info")
    file_structure_md = get_file_tree(repo_path, skip_dirs=ctx.skip_dirs, file_ext_filter=ctx.file_ext, max_depth=6)
    
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

    # Get detailed file descriptions using RAG
    echo_styled("Using RAG to retrieve detailed file descriptions...", "info")
    file_descriptions = "No detailed file descriptions available."
    active_embedder = None
    
    # First check for OPENAI_API_KEY which is required for embeddings
    if not os.getenv('OPENAI_API_KEY'):
        echo_styled("❌ OPENAI_API_KEY is not set. Cannot proceed without it.", "error")
        echo_styled("Set the OPENAI_API_KEY environment variable and try again.", "info")
        return
        
    # Initialize embedder if not already done
    if ctx.embedder is None:
        ctx.init_embedder()
    
    # Check if we have a working embedder now
    if ctx.embedder and ctx.embedder.vector_store:
        echo_styled("✅ Using existing embeddings for RAG.", "success")
        active_embedder = ctx.embedder
    else:
        # No working embedder yet, try to create one
        echo_styled("Checking for existing embeddings...", "info")
        try:
            # Initialize CodeEmbedder with repository path for proper metadata tracking
            embedder = CodeEmbedder(
                repo_path=repo_path,
            )
            
            # Try to load existing embeddings first
            if embedder.load_vector_store():
                echo_styled("✅ Using existing embeddings for RAG.", "success")
                active_embedder = embedder
                # Update context embedder
                ctx.embedder = embedder
            else:
                echo_styled("No existing embeddings found. Please run 'langdoc parse' first.", "error")
                echo_styled("Cannot generate README without embeddings.", "info")
                return
        except Exception as e:
            echo_styled(f"❌ Error initializing embedder: {e}", "error")
            echo_styled("Cannot proceed without working embeddings.", "info")
            return

    # Use the active embedder to generate file descriptions
    file_descriptions_parts = []
    if active_embedder:
        # Get descriptions for up to 5 most important files
        important_file_patterns = [
            "main", "app", "index", "core", "model", "util", "config", "client", "server"
        ]
        found_files = []
        
        # First search for common important file patterns
        for pattern in important_file_patterns:
            if len(found_files) >= 5:  # Limit to 5 important files for brevity
                break
                
            query = f"file:{pattern} type:function"
            try:
                # For each file, get a brief description using RAG
                results = active_embedder.similarity_search(query, k=3)
                for doc in results:
                    filepath = doc.metadata.get('filepath', '')
                    if filepath and filepath not in [f['file'] for f in found_files]:
                        found_files.append({
                            'file': filepath,
                            'description': readme_generator.generate_file_description(
                                doc.page_content, os.path.basename(filepath)
                            )
                        })
            except Exception as e:
                echo_styled(f"Error getting file description for pattern '{pattern}': {e}", "warning")

        # Add the descriptions to our list
        for file_info in found_files:
            # Just use the basename as the document name
            doc_name = os.path.basename(file_info['file'])
            file_descriptions_parts.append(f"- `{doc_name}`: {file_info['description']}")     
    file_descriptions = "\n".join(file_descriptions_parts) if file_descriptions_parts else "No detailed file descriptions available."

    # Generate the complete README content using ReadmeGenerator
    echo_styled("Generating README content...", "info")
    readme_content = readme_generator.generate_readme(
        project_name=project_name,
        file_structure=file_structure_md,
        key_elements_summary=key_elements_summary,
        file_descriptions=file_descriptions
    )

    try:
        with open(os.path.join(repo_path, output_file), 'w', encoding='utf-8') as f:
            f.write(readme_content)
        echo_styled(f"README generated/updated at {os.path.join(repo_path, output_file)}", "success")
    except IOError as e:
        echo_styled(f"Error writing README to {os.path.join(repo_path, output_file)}: {e}", "error")
