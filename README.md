# langdoc

## Project Overview: langdoc

The 'langdoc' project is a comprehensive tool designed to analyze and document Git repositories using LangChain and RAG. It consists of multiple components and files that work together to achieve this functionality.

### Project Summary
The main functionality of 'langdoc' is to provide a CLI tool that can analyze Git repositories and generate detailed documentation using LangChain and RAG. This tool aims to automate the process of analyzing codebases and extracting meaningful insights for documentation purposes.

### Key Files and Their Purposes

1. **docgen.py**
   - **Purpose:** This file contains the core functionality for generating documentation. It includes instructions for analyzing the project context, writing informative sections, and incorporating specific details about major files and components.
   - **Key Sections:** 
     - Instructions for developing a deep understanding of the project.
     - Guidelines for writing informative sections with proper markdown formatting.
     - Details on major file descriptions and their purposes.
     - Project summary guidelines and file structure explanations.

2. **cli/main.py**
   - **Purpose:** This file defines the CLI functionality for the 'langdoc' tool. It contains the `cli` function that initializes a custom context object for Click's context.
   - **Key Components:**
     - `cli` function: Initializes the LangDocContext object for Click's context.
     - Docstring: Describes 'LangDoc' as a CLI tool for analyzing and documenting Git repositories using LangChain and RAG.

### File Structure Overview
The file structure of the 'langdoc' project is organized to support the main functionality of analyzing and documenting Git repositories. Specific details about the file structure are provided within the project files themselves.

## File Structure

The 'langdoc' project's file structure is designed to support the analysis and documentation of Git repositories. Below is an overview of the key directories and files within the project:

- **.langdoc_db/**
  - Directory containing the LangDoc database files for storing project metadata.

- **cli/**
  - Directory housing the CLI functionality for the 'langdoc' tool.
  - **__init__.py**
  - **commands/**
    - Directory containing CLI command implementations.
    - **ask_cmd.py**
    - **doc_cmd.py**
    - **parse_cmd.py**
    - **readme_cmd.py**
  - **context.py**
  - **main.py**
  - **utils.py**

- **cli.py**
  - Main CLI script for executing 'langdoc' commands.

- **docgen.py**
  - Core functionality for generating project documentation.
  - Contains functions for analyzing project context and writing informative sections.

- **embedding.py**
  - Functionality for extracting repository metadata and embedding code.
  - **get_repo_metadata** function for retrieving repository metadata.
  - **CodeEmbedder** class for embedding code snippets.

- **parser.py**
  - Functions for parsing Python files and retrieving file paths.

- **utils.py**
  - Utility functions for loading configuration, retrieving project name, and accessing configuration values.

The file structure is organized to facilitate the analysis and documentation process, with each file serving a specific purpose in the overall functionality of the 'langdoc' tool.

## Notable Classes/Functions

### `DocGenerator` (class) in `docgen.py`
- **Purpose:** Responsible for generating documentation for Git repositories using LangChain and RAG.
- **Key Functions:**
  - `__init__` (function): Initializes the DocGenerator class.
  - `generate_docstring` (function): Generates docstrings for the analyzed code.
  
### `CodeEmbedder` (class) in `embedding.py`
- **Purpose:** Handles embedding code snippets into the documentation.
- **Key Functions:**
  - `__init__` (function): Initializes the CodeEmbedder class.
  - `get_repo_metadata` (function): Retrieves metadata information from the repository.

### `LangDocContext` (class) in `context.py`
- **Purpose:** Defines the context for the LangDoc CLI tool.
- **Key Functions:**
  - `__init__` (function): Initializes the LangDocContext class.
  - `init_from_repo_path` (function): Initializes the context from the repository path.

### Other Functions:
- `get_file_paths` (function) in `parser.py`: Retrieves file paths for parsing.
- `parse_python_file` (function) in `parser.py`: Parses Python files for analysis.
- `load_config` (function) in `utils.py`: Loads configuration settings for the tool.
- `get_config_value` (function) in `utils.py`: Retrieves specific configuration values.
- `get_project_name` (function) in `utils.py`: Retrieves the project name for documentation purposes.

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
