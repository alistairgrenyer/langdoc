# parser.py
import os
import ast
from typing import List, Dict, Any, Optional
import git  # Added for .gitignore handling

# Placeholder for more sophisticated parsing if needed

def get_file_paths(repo_path: str, file_ext: str = '.py', skip_dirs: Optional[List[str]] = None) -> List[str]:
    """Recursively get all file paths with a given extension in a directory,
    skipping specified subdirectories and respecting .gitignore rules if present."""
    print(f"DEBUG_PARSER: get_file_paths called with repo_path='{repo_path}', file_ext='{file_ext}', skip_dirs={skip_dirs}")

    effective_skip_dirs = skip_dirs if skip_dirs is not None else ['.git', '.venv', '__pycache__', 'node_modules', '.vscode', '.idea', 'dist', 'build', 'docs']
    print(f"DEBUG_PARSER: Effective skip_dirs being used: {effective_skip_dirs}")

    collected_file_paths = []
    abs_repo_path = os.path.abspath(repo_path)
    print(f"DEBUG_PARSER: Absolute repo_path: {abs_repo_path}")
    
    git_repo_obj = None
    git_working_dir = None

    try:
        repo_candidate = git.Repo(abs_repo_path, search_parent_directories=True)
        git_working_dir = os.path.abspath(repo_candidate.working_tree_dir)
        git_repo_obj = repo_candidate
        print(f"DEBUG_PARSER: Git repository initialized. Working tree: {git_working_dir}")
    except git.exc.InvalidGitRepositoryError:
        print(f"DEBUG_PARSER: INFO: '{abs_repo_path}' is not a valid git repository. .gitignore rules from git library will not be applied.")
        pass  
    except Exception as _e:
        print(f"DEBUG_PARSER: WARNING: Could not initialize Git repository at '{abs_repo_path}': {_e}. .gitignore rules from git library will not be applied.")
        pass

    for root, dirs, files in os.walk(abs_repo_path, topdown=True):
        abs_root = os.path.abspath(root)
        print(f"\nDEBUG_PARSER: --- Walking in abs_root: {abs_root} ---")
        print(f"DEBUG_PARSER: Initial dirs: {dirs}")

        # 1. Filter directories based on skip_dirs (simple name matching on directory name)
        original_dirs_before_skip_filter = list(dirs)
        dirs[:] = [d for d in dirs if d not in effective_skip_dirs]
        print(f"DEBUG_PARSER: Dirs after 'effective_skip_dirs' filter (removed {set(original_dirs_before_skip_filter) - set(dirs)}): {dirs}")

        # 2. Filter directories further based on .gitignore rules (if git_repo_obj is available)
        if git_repo_obj and git_working_dir:
            current_dirs_before_git_filter = list(dirs) 
            dirs[:] = [] 
            for d_name in current_dirs_before_git_filter:
                dir_path_abs = os.path.join(abs_root, d_name)
                dir_path_rel_to_git_root = os.path.relpath(dir_path_abs, git_working_dir).replace(os.sep, '/')
                try:
                    is_ignored_by_git = git_repo_obj.is_ignored(dir_path_rel_to_git_root)
                    print(f"DEBUG_PARSER: Git check for DIR '{dir_path_rel_to_git_root}': Ignored = {is_ignored_by_git}")
                    if not is_ignored_by_git:
                        dirs.append(d_name)
                except Exception as _e:
                    print(f"DEBUG_PARSER: WARNING: Error checking if DIR '{dir_path_rel_to_git_root}' is ignored: {_e}. Including directory.")
                    dirs.append(d_name) # If error, include directory (conservative)
            print(f"DEBUG_PARSER: Dirs after .gitignore filter (removed {set(current_dirs_before_git_filter) - set(dirs)}): {dirs}")
        
        # Process files in the current, non-ignored directory
        for file_name in files:
            if file_name.endswith(file_ext):
                file_path_abs = os.path.join(abs_root, file_name)
                print(f"DEBUG_PARSER: Considering file: {file_path_abs}")
                
                is_file_ignored_by_git = False
                if git_repo_obj and git_working_dir:
                    file_path_rel_to_git_root = os.path.relpath(file_path_abs, git_working_dir).replace(os.sep, '/')
                    try:
                        is_ignored_by_git = git_repo_obj.is_ignored(file_path_rel_to_git_root)
                        print(f"DEBUG_PARSER: Git check for FILE '{file_path_rel_to_git_root}': Ignored = {is_ignored_by_git}")
                        if is_ignored_by_git:
                            is_file_ignored_by_git = True
                    except Exception as _e:
                        print(f"DEBUG_PARSER: WARNING: Error checking if FILE '{file_path_rel_to_git_root}' is ignored: {_e}. Assuming not ignored.")
                        pass 
                
                if not is_file_ignored_by_git:
                    print(f"DEBUG_PARSER: ADDING file: {file_path_abs}")
                    collected_file_paths.append(file_path_abs)
                else:
                    print(f"DEBUG_PARSER: SKIPPING (git-ignored) file: {file_path_abs}")
            # else:
                # print(f"DEBUG_PARSER: File {file_name} does not match extension {file_ext}")

    print(f"DEBUG_PARSER: get_file_paths returning {len(collected_file_paths)} files.")
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

if __name__ == '__main__':
    # Example usage:
    sample_repo_path = '.' # Current directory, adjust as needed
    py_files = get_file_paths(sample_repo_path, skip_dirs=['.git', 'venv', '__pycache__', 'docs'])
    print(f"Found {len(py_files)} Python files.")

    for py_file in py_files:
        if os.path.basename(py_file) not in [os.path.basename(__file__), 'cli.py', 'embedding.py', 'docgen.py', 'utils.py']:
            print(f"\nParsing: {py_file}")
            parsed_data = parse_python_file(py_file)
            if "error" in parsed_data:
                print(f"  Error: {parsed_data['error']}")
            else:
                for definition in parsed_data['definitions']:
                    print(f"  - {definition['type'].capitalize()} {definition['name']} (lines {definition['lineno']}-{definition['end_lineno']})")
                    # print(f"    Docstring: {definition['docstring']}")
                    # print(f"    Code:\n{definition['code']}\n")

