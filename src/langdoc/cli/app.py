"""Main CLI application using Typer."""

import os
from pathlib import Path
from typing import Optional

import rich.console
import typer
from typing_extensions import Annotated

from langdoc.application.services import CodebaseAnalysisService, DocumentationGeneratorService
from langdoc.cli.commands import GenerateReadmeCommand, IndexCodebaseCommand
from langdoc.domain.models import DocumentType
from langdoc.infrastructure.embeddings.vector_store import CodeVectorStore
from langdoc.infrastructure.filesystem.filesystem_service import FilesystemService
from langdoc.infrastructure.git.git_service import GitRepositoryService
from langdoc.infrastructure.llm.llm_service import LLMDocumentationService, ReadmeGenerationLLMService

app = typer.Typer(
    name="langdoc",
    help="Generate documentation for codebases using LLMs and RAG.",
    add_completion=False,
)

# Initialize shared console
console = rich.console.Console()


@app.command()
def readme(
    path: Annotated[
        Optional[Path],
        typer.Argument(
            help="Path to the codebase. Defaults to current directory.",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output", "-o",
            help="Output path for the README.md file.",
            file_okay=False,
            dir_okay=True,
        ),
    ] = None,
    use_rag: Annotated[
        bool,
        typer.Option(
            "--rag/--no-rag",
            help="Whether to use RAG (Retrieval Augmented Generation) for generation.",
        ),
    ] = True,
    model: Annotated[
        str,
        typer.Option(
            "--model", "-m",
            help="Name of the LLM model to use.",
        ),
    ] = "gpt-3.5-turbo",
    api_key: Annotated[
        Optional[str],
        typer.Option(
            "--api-key",
            help="OpenAI API key. Defaults to OPENAI_API_KEY environment variable.",
            envvar="OPENAI_API_KEY",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose", "-v",
            help="Enable verbose output.",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet", "-q",
            help="Suppress all output except errors.",
        ),
    ] = False,
):
    """Generate a README.md file for a codebase."""
    # Set up directory paths
    codebase_path = Path(path or os.getcwd()).resolve()
    output_path = Path(output or codebase_path).resolve()
    
    # Set console level based on verbosity flags
    if quiet:
        console.quiet = True
    if verbose:
        console.print("[yellow]Verbose mode enabled[/yellow]")
        
    # Check API key
    if not api_key and not os.environ.get("OPENAI_API_KEY"):
        console.print(
            "[bold red]Error:[/bold red] No OpenAI API key provided. "
            "Set OPENAI_API_KEY environment variable or use --api-key option."
        )
        raise typer.Exit(code=1)
        
    try:
        # Initialize services
        filesystem_service = FilesystemService(console=console)
        git_service = GitRepositoryService(console=console)
        
        # Initialize vector store for RAG if enabled
        vector_store = None
        if use_rag:
            console.print("[green]Initializing vector store for RAG...[/green]")
            vector_store = CodeVectorStore(console=console)
            
            # Index codebase
            index_command = IndexCodebaseCommand(
                vector_store=vector_store,
                codebase_path=codebase_path,
                console=console,
            )
            index_command.execute()
        
        # Initialize LLM service
        llm_service = ReadmeGenerationLLMService(
            model_name=model,
            api_key=api_key,
            console=console,
            streaming=not quiet,
        )
        
        # Initialize application services
        analyzer = CodebaseAnalysisService(
            filesystem=filesystem_service,
            git_service=git_service,
            vector_store=vector_store,
            console=console,
        )
        generator = DocumentationGeneratorService(
            llm_service=llm_service,
            vector_store=vector_store,
            console=console,
        )
        
        # Create and execute command
        command = GenerateReadmeCommand(
            analyzer=analyzer,
            generator=generator,
            codebase_path=codebase_path,
            output_path=output_path,
            console=console,
        )
        readme_path = command.execute()
        
        if not quiet:
            # Display success message
            console.print(f"[bold green]README.md generated successfully at:[/bold green] {readme_path}")
        
    except Exception as e:
        if not quiet:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show the version of LangDoc."""
    from langdoc import __version__
    console.print(f"LangDoc version: {__version__}")


if __name__ == "__main__":
    app()
