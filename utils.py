# utils.py
import os
import json
from typing import List, Dict, Any, Optional

CONFIG_FILE_NAME = ".gitdocrc"

def load_config(repo_path: str) -> Dict[str, Any]:
    """Loads configuration from .gitdocrc file in the repo_path."""
    config_path = os.path.join(repo_path, CONFIG_FILE_NAME)
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Could not parse {CONFIG_FILE_NAME}. Using default settings.")
        except Exception as e:
            print(f"Error loading {CONFIG_FILE_NAME}: {e}. Using default settings.")
    return {}

def get_config_value(config: Dict[str, Any], key: str, default: Any) -> Any:
    """Safely gets a value from the loaded config or returns default."""
    return config.get(key, default)

def get_project_name(repo_path: str) -> str:
    """Derives a project name from the repository path."""
    return os.path.basename(os.path.abspath(repo_path))


def get_file_tree(start_path: str, skip_dirs: Optional[List[str]] = None, file_ext_filter: Optional[str] = None, max_depth: int = 3, indent_char: str = '  ') -> str:
    """Generates a string representation of the file tree.
    
    Args:
        start_path: The root directory to start from.
        skip_dirs: A list of directory names to skip.
        file_ext_filter: If provided, only include files with this extension.
        max_depth: Maximum depth to traverse.
        indent_char: String to use for indentation.
    Returns:
        A string representing the file tree.
    """
    if skip_dirs is None:
        skip_dirs = ['.git', 'venv', '__pycache__', 'node_modules', '.vscode', '.idea', 'dist', 'build']
    
    lines = []

    def _recurse_tree(current_path, current_depth, prefix=""):
        if current_depth > max_depth:
            if os.path.isdir(current_path):
                 # Check if directory contains relevant files before adding ellipsis for too deep
                has_relevant_files = False
                for item in os.listdir(current_path):
                    item_path = os.path.join(current_path, item)
                    if os.path.isfile(item_path) and (not file_ext_filter or item.endswith(file_ext_filter)):
                        has_relevant_files = True
                        break
                    elif os.path.isdir(item_path) and item not in skip_dirs:
                        # A bit of a lookahead, not perfect but helps
                        has_relevant_files = True 
                        break
                if has_relevant_files:
                    lines.append(f"{prefix}{indent_char * (current_depth -1)}└── ... (too deep)")
            return

        items = sorted(os.listdir(current_path))
        entries = []
        for item in items:
            item_path = os.path.join(current_path, item)
            if os.path.isdir(item_path):
                if item not in skip_dirs:
                    entries.append((item, True))
            elif os.path.isfile(item_path):
                if not file_ext_filter or item.endswith(file_ext_filter):
                    entries.append((item, False))
        
        for i, (name, is_dir) in enumerate(entries):
            connector = "├── " if i < len(entries) - 1 else "└── "
            lines.append(f"{prefix}{connector}{name}{'/' if is_dir else ''}")
            if is_dir:
                new_prefix = prefix + ("│   " if i < len(entries) - 1 else "    ")
                _recurse_tree(os.path.join(current_path, name), current_depth + 1, new_prefix)

    lines.append(f"{os.path.basename(os.path.abspath(start_path))}/")
    _recurse_tree(start_path, 1, "")
    return "\n".join(lines)
