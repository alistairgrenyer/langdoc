"""
Documentation generation command implementation for langdoc CLI.
"""
import os
import click
from langdoc.core.generators.doc import DocGenerator
from langdoc.cli.context import pass_langdoc_ctx, LangDocContext
from langdoc.cli.utils import echo_styled, get_parsed_files, validate_api_key, create_directory_if_not_exists


@click.command()
@click.option('--path', 'repo_path', default='.', 
              help='Path to the Git repository.', 
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), 
              show_default=True)
@click.option('--output-dir', default='docs', 
              help='Directory to save generated documentation.', 
              type=click.Path(file_okay=False, writable=True), 
              show_default=True)
@click.option('--update-docstrings', is_flag=True, 
              help='Attempt to update docstrings in source files (currently prints suggestions).')
@pass_langdoc_ctx
def doc(ctx: LangDocContext, repo_path: str, output_dir: str, update_docstrings: bool):
    """Generate code comments and markdown documentation."""
    echo_styled(f"--- Starting Documentation Generation for: {os.path.abspath(repo_path)} ---", "header")

    # Validate API key - will exit if not present
    validate_api_key("OPENAI_API_KEY", "Cannot proceed with documentation generation.")

    # Initialize context with repository path
    ctx.init_from_repo_path(repo_path)
    
    # Initialize doc generator
    llm_model = ctx.config.get('llm_model', 'gpt-3.5-turbo')
    doc_generator = DocGenerator(model_name=llm_model)

    # Parse files
    parsed_files = get_parsed_files(repo_path, ctx.file_ext, ctx.skip_dirs)
    if not parsed_files:
        echo_styled("No files parsed. Aborting documentation generation.", "warning")
        return

    # Create output directory if needed
    create_directory_if_not_exists(output_dir)

    # Generate markdown documentation
    echo_styled(f"Generating markdown documentation for {len(parsed_files)} files into '{output_dir}'...", "info")
    generated_md_files = []
    
    with click.progressbar(parsed_files, label='Generating module docs') as bar:
        for pf_data in bar:
            if update_docstrings:
                echo_styled(f"Checking/Updating docstrings for {pf_data['file_path']}...", "info")
                # This currently prints suggestions, actual file modification is complex
                doc_generator.update_file_with_docstrings(pf_data['file_path'], pf_data)
            
            md_file_path = doc_generator.generate_module_markdown(pf_data, output_dir=output_dir)
            if md_file_path:
                generated_md_files.append(md_file_path)
    
    if generated_md_files:
        echo_styled(f"Successfully generated {len(generated_md_files)} markdown files in '{output_dir}'.", "success")
    else:
        echo_styled("No markdown files were generated.", "warning")
