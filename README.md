# langdoc

## Project Summary
## Project Summary

The **langdoc** project is a comprehensive tool designed to analyze and document Git repositories using LangChain and RAG. It consists of several key components that work together to achieve this goal:

### Key Functions/Classes Summary:
- `cli` (function) in `cli.py`: Handles the command-line interface for the tool.
- `DocGenerator` (class) in `docgen.py`: Generates code comments and markdown documentation.
- `CodeEmbedder` (class) in `embedding.py`: Embeds code snippets into documents using OpenAI embeddings.
- `parse_python_file` (function) in `parser.py`: Parses Python files to extract functions, classes, and their docstrings.
- `load_config` (function) in `utils.py`: Loads configuration settings for the tool.

### File Structure Overview:
- **cli.py**: Contains the CLI functionality for the tool.
- **docgen.py**: Implements the `DocGenerator` class for generating documentation.
- **embedding.py**: Includes the `CodeEmbedder` class for embedding code snippets.
- **parser.py**: Provides functions for parsing Python files.
- **utils.py**: Contains utility functions for loading configurations and common options.

Each component plays a crucial role in the overall functionality of the **langdoc** tool, working together to analyze and document code repositories effectively.

## File Structure
### File Structure

The `langdoc` project consists of the following files:

- `cli.py`: Contains functions related to the command-line interface of the tool.
- `docgen.py`: Includes functions for generating code comments and markdown documentation.
- `embedding.py`: Defines a class for embedding text using OpenAI's model and text splitting techniques.
- `parser.py`: Provides functions for parsing Python files and extracting functions, classes, and their docstrings.
- `utils.py`: Contains utility functions for loading configuration, getting common options, and retrieving project names.

Each file serves a specific purpose in the overall functionality of the `langdoc` project.

## Notable Classes/Functions
### Notable Classes/Functions

#### `cli.py`
- **cli** (function)
  - Description: A CLI tool to analyze and document Git repositories using LangChain and RAG.
  - Code: 
    ```python
    def cli(ctx):
        ctx.ensure_object(dict)
        # Load config once and pass it around if needed, or load per command
        # For simplicity, we'll load config within commands that need it.
        pass
    ```

#### `docgen.py`
- **DocGenerator** (class)
  - Description: Generates code comments and markdown documentation.
  - Code: 
    ```python
    class DocGenerator:
        def __init__(self):
            pass
        
        def generate_docstring(self):
            pass
    ```

#### `embedding.py`
- **CodeEmbedder** (class)
  - Description: Embeds code using OpenAI embeddings and text splitting techniques.
  - Code: 
    ```python
    class CodeEmbedder:
        def __init__(self, model_name="text-embedding-ada-002", chunk_size=1000, chunk_overlap=100):
            pass
        
        def create_documents_from_parsed_data(self):
            pass
    ```

#### `parser.py`
- **parse_python_file** (function)
  - Description: Parses a Python file and extracts functions, classes, and their docstrings.
  - Code: 
    ```python
    def parse_python_file(file_path: str) -> Dict[str, Any]:
        pass
    ```

#### `utils.py`
- **load_config** (function)
  - Description: Loads configuration settings for the project.
  - Code: 
    ```python
    def load_config(repo_path: str) -> Dict[str, Any]:
        pass
    ```

- **get_config_value** (function)
  - Description: Retrieves a specific value from the project's configuration.
  - Code: 
    ```python
    def get_config_value(config: Dict[str, Any], key: str, default: Any):
        pass
    ```

- **get_project_name** (function)
  - Description: Retrieves the project name from the configuration.
  - Code: 
    ```python
    def get_project_name(repo_path: str) -> str:
        pass
    ```

## Setup and Usage

### Setup

1.  Clone the repository:
    ```bash
    git clone <your-repo-url>
    cd langdoc
    ```


2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. Set up environment variables:
   Copy `.env.example` to `.env` and fill in your API keys (e.g., `OPENAI_API_KEY`).
   ```bash
   cp .env.example .env
   ```

### Running LangDoc Commands

Once setup, you can use the LangDoc CLI:

-   **Parse the repository and build embeddings:**
    ```bash
    python cli.py parse --path /path/to/your/repo
    ```
-   **Generate documentation:**
    ```bash
    python cli.py doc --path /path/to/your/repo --output-dir project_docs
    ```
-   **Ask questions about the code:**
    ```bash
    python cli.py ask "How does the authentication work?" --path /path/to/your/repo
    ```
-   **Refresh this README:**
    ```bash
    python cli.py readme --path /path/to/your/repo
    ```
