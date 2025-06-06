# langdoc

## Project Summary
## Project Summary

The `langdoc` project is a tool for generating documentation from Python code. It consists of several key functions and classes:

- `cli` (function) in `cli.py`: Handles command-line interface functionality.
- `get_common_options` (function) in `cli.py`: Retrieves common options for the CLI.
- `_get_parsed_files` (function) in `cli.py`: Parses files for documentation generation.
- `DocGenerator` (class) in `docgen.py`: Generates documentation from parsed data.
- `generate_docstring` (function) in `docgen.py`: Generates docstrings for code elements.
- `CodeEmbedder` (class) in `embedding.py`: Embeds code snippets into documentation.
- `create_documents_from_parsed_data` (function) in `embedding.py`: Creates documents from parsed data.
- `get_file_paths` (function) in `parser.py`: Retrieves file paths for parsing.
- `parse_python_file` (function) in `parser.py`: Parses Python files for documentation extraction.
- `load_config` (function) in `utils.py`: Loads configuration settings for the project.
- `get_config_value` (function) in `utils.py`: Retrieves specific values from the configuration.
- `get_project_name` (function) in `utils.py`: Retrieves the name of the project.

## File Structure

```
langdoc/
├── cli.py
├── docgen.py
├── embedding.py
├── parser.py
└── utils.py
```

## Notable Classes/Functions

- `cli` (function) in `cli.py`
- `get_common_options` (function) in `cli.py`
- `_get_parsed_files` (function) in `cli.py`
- `DocGenerator` (class) in `docgen.py`
- `__init__` (function) in `docgen.py`
- `generate_docstring` (function) in `docgen.py`
- `CodeEmbedder` (class) in `embedding.py`
- `__init__` (function) in `embedding.py`
- `create_documents_from_parsed_data` (function) in `embedding.py`
- `get_file_paths` (function) in `parser.py`
- `parse_python_file` (function) in `parser.py`
- `load_config` (function) in `utils.py`
- `get_config_value` (function) in `utils.py`
- `get_project_name` (function) in `utils.py`

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
