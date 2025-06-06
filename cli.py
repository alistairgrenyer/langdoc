#!/usr/bin/env python
"""
LangDoc CLI - A tool to analyze and document Git repositories using LangChain and RAG.

This is a thin wrapper around the modular CLI structure defined in the cli/ package.
All CLI commands have been moved to the modular structure in the cli/ directory.
"""

# Import the main CLI from the new modular structure
from cli.main import cli

# Add an entry point to make the module directly executable
if __name__ == "__main__":
    cli()
