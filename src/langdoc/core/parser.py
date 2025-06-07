# parser.py
import os
import ast
import subprocess
from typing import List, Dict, Any, Optional
import git  # Added for .gitignore handling

# Placeholder for more sophisticated parsing if needed

def get_file_paths(repo_path: str, file_ext: str = '.py', skip_dirs: Optional[List[str]] = None) -> List[str]:
    """Recursively get all file paths with a given extension in a directory,
    skipping specified subdirectories and respecting .gitignore rules if present."""
    effective_skip_dirs = skip_dirs if skip_dirs is not None else ['.git', '.venv', '__pycache__', 'node_modules', '.vscode', '.idea', 'dist', 'build', 'docs']
    
    collected_file_paths = []
    abs_repo_path = os.path.abspath(repo_path)
    
    git_repo_obj = None
    git_working_dir = None

    try:
        repo_candidate = git.Repo(abs_repo_path, search_parent_directories=True)
        git_working_dir = os.path.abspath(repo_candidate.working_tree_dir)
        git_repo_obj = repo_candidate
    except git.InvalidGitRepositoryError:
        pass  
    except Exception as _e:
        pass

    for root, dirs, files in os.walk(abs_repo_path, topdown=True):
        abs_root = os.path.abspath(root)
        # 1. Filter directories based on skip_dirs (simple name matching on directory name)
        dirs[:] = [d for d in dirs if d not in effective_skip_dirs]

        # 2. Filter directories further based on .gitignore rules (if git_repo_obj is available)
        if git_repo_obj and git_working_dir:
            current_dirs_before_git_filter = list(dirs) 
            dirs[:] = [] 
            for d_name in current_dirs_before_git_filter:
                dir_path_abs = os.path.join(abs_root, d_name)
                dir_path_rel_to_git_root = os.path.relpath(dir_path_abs, git_working_dir).replace(os.sep, '/')
                try:
                    # Check if path is ignored using git check-ignore command
                    # GitPython dynamically generates this method from git's CLI commands
                    try:
                        # First approach: Using GitPython's git interface
                        is_ignored_output = git_repo_obj.git.check_ignore(dir_path_rel_to_git_root)
                        is_ignored_by_git = bool(is_ignored_output.strip())
                    except AttributeError:
                        # Fallback: Run git check-ignore directly using subprocess
                        try:
                            result = subprocess.run(['git', 'check-ignore', dir_path_rel_to_git_root], 
                                                    cwd=git_working_dir,
                                                    stdout=subprocess.PIPE, 
                                                    stderr=subprocess.PIPE,
                                                    text=True)
                            # Exit code 0 means path is ignored, 1 means not ignored
                            is_ignored_by_git = result.returncode == 0 and bool(result.stdout.strip())
                        except Exception:
                            is_ignored_by_git = False
                            
                    if not is_ignored_by_git:
                        dirs.append(d_name)
                except Exception as _e:
                    dirs.append(d_name) # If error, include directory (conservative)
        
        # Process files in the current, non-ignored directory
        for file_name in files:
            if file_name.endswith(file_ext):
                file_path_abs = os.path.join(abs_root, file_name)
                
                is_file_ignored_by_git = False
                if git_repo_obj and git_working_dir:
                    file_path_rel_to_git_root = os.path.relpath(file_path_abs, git_working_dir).replace(os.sep, '/')
                    try:
                        # Check if file is ignored using git check-ignore command
                        try:
                            # First approach: Using GitPython's git interface
                            is_ignored_output = git_repo_obj.git.check_ignore(file_path_rel_to_git_root)
                            is_ignored_by_git = bool(is_ignored_output.strip())
                        except AttributeError:
                            # Fallback: Run git check-ignore directly using subprocess
                            try:
                                result = subprocess.run(['git', 'check-ignore', file_path_rel_to_git_root], 
                                                        cwd=git_working_dir,
                                                        stdout=subprocess.PIPE, 
                                                        stderr=subprocess.PIPE,
                                                        text=True)
                                # Exit code 0 means path is ignored, 1 means not ignored
                                is_ignored_by_git = result.returncode == 0 and bool(result.stdout.strip())
                            except Exception:
                                is_ignored_by_git = False
                                
                        if is_ignored_by_git:
                            is_file_ignored_by_git = True
                    except Exception as _e:
                        pass 
                
                if not is_file_ignored_by_git:
                    collected_file_paths.append(file_path_abs)

    return collected_file_paths

def parse_python_file(file_path: str) -> Dict[str, Any]:
    """Parses a Python file and extracts functions, classes, and their docstrings."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return {"file_path": file_path, "error": str(e), "definitions": []}

    definitions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            definitions.append({
                "type": "function",
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "lineno": node.lineno,
                "end_lineno": node.end_lineno,
                "code": ast.get_source_segment(content, node)
            })
        elif isinstance(node, ast.AsyncFunctionDef):
            definitions.append({
                "type": "async_function",
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "lineno": node.lineno,
                "end_lineno": node.end_lineno,
                "code": ast.get_source_segment(content, node)
            })
        elif isinstance(node, ast.ClassDef):
            definitions.append({
                "type": "class",
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "lineno": node.lineno,
                "end_lineno": node.end_lineno,
                "code": ast.get_source_segment(content, node)
                # Could also parse methods within the class here
            })
            
    return {
        "file_path": file_path,
        "content": content, # Full file content for context if needed
        "definitions": definitions
    }
