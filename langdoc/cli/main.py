"""
Main CLI entry point that registers all command modules.
"""
import click
from dotenv import load_dotenv

from langdoc.cli.context import LangDocContext
from langdoc.cli.commands.parse_cmd import parse
from langdoc.cli.commands.doc_cmd import doc
from langdoc.cli.commands.readme_cmd import readme
from langdoc.cli.commands.ask_cmd import ask

# Load .env file at startup
load_dotenv()


@click.group()
@click.pass_context
def cli(ctx):
    """LangDoc: A CLI tool to analyze and document Git repositories using LangChain and RAG."""
    # Initialize our custom context object and store it in Click's context
    ctx.obj = LangDocContext()


# Register all commands
cli.add_command(parse)
cli.add_command(doc)
cli.add_command(readme)
cli.add_command(ask)


if __name__ == '__main__':
    cli()
