"""
CLI utilities for common operations across commands.
"""
import os
import click
from typing import List, Dict, Any

from langdoc.core.parser import get_file_paths, parse_python_file


def echo_styled(message: str, style: str = "default", **kwargs) -> None:
    """Print styled messages with standardized formatting."""
    if style == "success":
        click.echo(click.style(message, fg='green', **kwargs))
    elif style == "error":
        click.echo(click.style(message, fg='red', **kwargs))
    elif style == "warning":
        click.echo(click.style(message, fg='yellow', **kwargs))
    elif style == "info":
        click.echo(click.style(message, fg='blue', **kwargs))
    elif style == "header":
        click.echo(click.style(message, bold=True, **kwargs))
    else:
        click.echo(message, **kwargs)


def get_parsed_files(repo_path: str, file_ext: str, skip_dirs: List[str]) -> List[Dict[str, Any]]:
    """Parse files from the repository and return structured data."""
    echo_styled(f"Scanning for {file_ext} files in '{repo_path}', skipping {skip_dirs}...", "info")
    
    file_paths = get_file_paths(repo_path, file_ext, skip_dirs)
    if not file_paths:
        echo_styled(f"No {file_ext} files found in '{repo_path}' (after skipping specified directories).", "warning")
        return []
    
    echo_styled(f"Found {len(file_paths)} {file_ext} files to parse.", "info")
    
    parsed_files_data = []
    with click.progressbar(file_paths, label='Parsing files') as bar:
        for f_path in bar:
            parsed_data = parse_python_file(f_path)
            if "error" in parsed_data:
                echo_styled(f"Error parsing {f_path}: {parsed_data['error']}", "error")
            elif parsed_data.get('definitions'):  # Only add files that have some definitions
                parsed_files_data.append(parsed_data)
    
    return parsed_files_data


def validate_api_key(key_name: str, purpose: str) -> None:
    """Validate if an API key is present and exit if not."""
    if not os.environ.get(key_name):
        echo_styled(f"{key_name} not found. {purpose}", "error")
        raise click.Abort(f"Missing required {key_name}. Cannot continue.")
    return None


def create_directory_if_not_exists(directory_path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        echo_styled(f"Created directory: {directory_path}", "info")
