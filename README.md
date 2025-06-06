# langdoc

## Project Summary

The `langdoc` project is a comprehensive tool designed for analyzing and documenting Git repositories using LangChain and RAG. It consists of a CLI interface with various commands to facilitate different functionalities. Here is a breakdown of key components and their functionalities:

- **DocGenerator** (class) in `docgen.py`: Responsible for generating code comments and markdown documentation.
- **CodeEmbedder** (class) in `embedding.py`: Handles creating documents from parsed data using OpenAI embeddings.
- **Parser** (functions) in `parser.py`: Parses Python files to extract functions, classes, and their docstrings.
- **LangDocContext** (class) in `context.py`: Manages the context of the LangDoc tool, including initialization from a repository path.

The project's main functionality is divided into separate commands within the `cli/commands` directory:
- **ask_cmd.py**: Allows asking high-level questions about the project using RAG.
- **doc_cmd.py**: Generates code comments and markdown documentation for a repository.
- **parse_cmd.py**: Parses the repository, builds, and saves embeddings.
- **readme_cmd.py**: Generates or updates the README.md file for the project.

Each file and component within the project serves a specific purpose in achieving the overall goal of analyzing and documenting Git repositories effectively. The seamless integration of these components ensures a streamlined workflow for users to extract valuable insights and documentation from their codebase.

```markdown
## File Structure

The `langdoc` project has the following file structure:

- `cli/`: Directory containing the command-line interface components
  - `__init__.py`
  - `commands/`: Subdirectory with command implementations
    - `__init__.py`
    - `ask_cmd.py`: Command for asking high-level questions about the project
    - `doc_cmd.py`: Command for generating code comments and markdown documentation
    - `parse_cmd.py`: Command for parsing the repository, building, and saving embeddings
    - `readme_cmd.py`: Command for generating or updating the README.md file
  - `context.py`: File containing the LangDocContext class
  - `main.py`: Main CLI entry point
  - `utils.py`: Utility functions for the CLI

- `cli.py`: Main CLI script
- `docgen.py`: File with the DocGenerator class and related functions
- `embedding.py`: File with the CodeEmbedder class and related functions
- `parser.py`: File with functions for parsing Python files
- `utils.py`: Utility functions for the project

Each significant file or directory serves the following purposes:

- `docgen.py`: Contains the DocGenerator class for generating code comments and markdown documentation.
- `embedding.py`: Includes the CodeEmbedder class for creating documents from parsed data.
- `parser.py`: Provides functions for extracting functions, classes, and docstrings from Python files.
- `utils.py`: Contains utility functions for loading configuration, getting project names, and other miscellaneous tasks.
- `context.py`: Defines the LangDocContext class for managing project context.
- `main.py`: Entry point for the CLI tool, initializing the LangDocContext object.
- `ask_cmd.py`: Implements the 'ask' command for high-level project questions using RAG.
- `doc_cmd.py`: Implements the 'doc' command for generating code comments and markdown documentation.
- `parse_cmd.py`: Implements the 'parse' command for parsing the repository and building embeddings.
- `readme_cmd.py`: Implements the 'readme' command for generating or updating the README.md file.
```

### Notable Classes/Functions

#### `DocGenerator` (class) in `docgen.py`
- Responsible for generating code comments and markdown documentation.

#### `CodeEmbedder` (class) in `embedding.py`
- Handles creating documents from parsed data using OpenAI embeddings.

#### `LangDocContext` (class) in `context.py`
- Manages the context of the LangDoc tool, including configuration and repository path initialization.

#### `generate_docstring` (function) in `docgen.py`
- Generates code comments and markdown documentation.

#### `create_documents_from_parsed_data` (function) in `embedding.py`
- Creates documents from parsed data using OpenAI embeddings.

#### `parse_python_file` (function) in `parser.py`
- Parses a Python file to extract functions, classes, and their docstrings.

#### `load_config` (function) in `utils.py`
- Loads the configuration settings for the LangDoc tool.

#### `get_config_value` (function) in `utils.py`
- Retrieves a specific configuration value.

#### `get_project_name` (function) in `utils.py`
- Retrieves the name of the project.

#### `init_from_repo_path` (function) in `context.py`
- Initializes the LangDoc context object from the repository path.

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
