"""
Main CLI entry point for langdoc.
This module serves as a thin wrapper importing and calling the actual CLI implementation.
"""
from langdoc.cli.main import cli

# Export the cli function directly for the entry point to work
__all__ = ['cli']

# This allows running with `python -m langdoc.cli` 
if __name__ == '__main__':
    cli()
