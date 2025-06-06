# langdoc

## Project Summary

The `langdoc` project is a comprehensive tool designed to analyze and document Git repositories using LangChain and RAG. It consists of key functions and classes spread across multiple files to facilitate the parsing, embedding, and generation of documentation for Python codebases.

### Key Functions/Classes Summary:
- `cli` (function) in `cli.py`: Responsible for initializing the CLI tool and loading necessary configurations.
- `DocGenerator` (class) in `docgen.py`: Handles the generation of code comments and markdown documentation.
- `CodeEmbedder` (class) in `embedding.py`: Manages the embedding of text using OpenAI's embeddings model.
- `parse_python_file` (function) in `parser.py`: Parses Python files to extract functions, classes, and their docstrings.
- `load_config` (function) in `utils.py`: Loads configuration settings for the tool.

### File Structure Overview:
- `cli.py`: Contains the CLI initialization function and related utilities.
- `docgen.py`: Houses the `DocGenerator` class for generating documentation.
- `embedding.py`: Includes the `CodeEmbedder` class for text embedding functionalities.
- `parser.py`: Provides functions for parsing Python files.
- `utils.py`: Contains utility functions for loading configurations and common options.

Each component plays a crucial role in the overall functionality of `langdoc`, working together to streamline the process of code analysis and documentation generation.

### File Structure

The `langdoc` project consists of the following files:

- `cli.py`: Contains functions related to the command-line interface.
- `docgen.py`: Includes functions for generating code comments and markdown documentation.
- `embedding.py`: Contains a class for text embedding and related functions.
- `parser.py`: Includes functions for parsing Python files and extracting functions, classes, and docstrings.
- `utils.py`: Contains utility functions for common options and configuration handling.

### Notable Classes/Functions

#### `cli.py`
- **cli (function)**
  - Description: A CLI tool to analyze and document Git repositories using LangChain and RAG.
  - File Path: C:\Users\Alist\Projects\langdoc\cli.py

- **get_common_options (function)**
  - Description: Retrieves common options for the CLI tool.
  - File Path: C:\Users\Alist\Projects\langdoc\cli.py

- **_get_parsed_files (function)**
  - Description: Parses files and extracts relevant information.
  - File Path: C:\Users\Alist\Projects\langdoc\cli.py

#### `docgen.py`
- **DocGenerator (class)**
  - Description: Generates code comments and markdown documentation.
  - File Path: C:\Users\Alist\Projects\langdoc\docgen.py

- **__init__ (function)**
  - Description: Initializes the DocGenerator class.
  - File Path: C:\Users\Alist\Projects\langdoc\docgen.py

- **generate_docstring (function)**
  - Description: Generates code comments and markdown documentation.
  - File Path: C:\Users\Alist\Projects\langdoc\docgen.py

#### `embedding.py`
- **CodeEmbedder (class)**
  - Description: Embeds code using a specified model.
  - File Path: C:\Users\Alist\Projects\langdoc\embedding.py

- **__init__ (function)**
  - Description: Initializes the CodeEmbedder class with specified parameters.
  - File Path: C:\Users\Alist\Projects\langdoc\embedding.py

- **create_documents_from_parsed_data (function)**
  - Description: Creates documents from parsed data using embeddings.
  - File Path: C:\Users\Alist\Projects\langdoc\embedding.py

#### `parser.py`
- **get_file_paths (function)**
  - Description: Retrieves file paths for parsing.
  - File Path: C:\Users\Alist\Projects\langdoc\parser.py

- **parse_python_file (function)**
  - Description: Parses a Python file and extracts functions, classes, and their docstrings.
  - File Path: C:\Users\Alist\Projects\langdoc\parser.py

#### `utils.py`
- **load_config (function)**
  - Description: Loads configuration settings for the tool.
  - File Path: C:\Users\Alist\Projects\langdoc\utils.py

- **get_config_value (function)**
  - Description: Retrieves a specific value from the loaded configuration.
  - File Path: C:\Users\Alist\Projects\langdoc\utils.py

- **get_project_name (function)**
  - Description: Retrieves the project name from the configuration.
  - File Path: C:\Users\Alist\Projects\langdoc\utils.py

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
