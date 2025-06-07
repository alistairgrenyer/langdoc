# langdoc

## Project Summary

The **langdoc** project is a comprehensive tool designed to assist users in language documentation tasks. With a well-organized file structure, the project offers key functions and classes that streamline the process of generating documentation for various languages. 

### Key Functions/Classes Summary:
- `LangDocContext` (class) in `context.py`
- `__init__` (function) in `context.py`
- `init_from_repo_path` (function) in `context.py`
- `cli` (function) in `main.py`
- `echo_styled` (function) in `utils.py`
- `get_parsed_files` (function) in `utils.py`
- `validate_api_key` (function) in `utils.py`
- `ask` (function) in `ask_cmd.py`
- `doc` (function) in `doc_cmd.py`

The project structure includes a `cli` module for command-line interface functionality, a `core` module for core functionalities like document generation and parsing, and a `utils` module for common utility functions. 

Explore the various modules and functions to leverage the power of **langdoc** in your language documentation endeavors.

### File Structure

```
langdoc/
├── setup.py
└── src/
    └── langdoc/
        ├── __init__.py
        ├── cli/
        │   ├── __init__.py
        │   ├── commands/
        │   │   ├── __init__.py
        │   │   ├── ask_cmd.py
        │   │   ├── doc_cmd.py
        │   │   ├── parse_cmd.py
        │   │   └── readme_cmd.py
        │   ├── context.py
        │   ├── main.py
        │   └── utils.py
        ├── cli.py
        ├── core/
        │   ├── __init__.py
        │   ├── docgen.py
        │   ├── embedding.py
        │   └── parser.py
        └── utils/
            ├── __init__.py
            └── common.py
```

- `setup.py`: Project setup file.
- `src/`: Source code directory.
  - `langdoc/`: Main package directory.
    - `__init__.py`: Initialization file.
    - `cli/`: Command-line interface package.
      - `__init__.py`: Initialization file.
      - `commands/`: Command modules package.
        - `ask_cmd.py`: Module for asking commands.
        - `doc_cmd.py`: Module for documentation commands.
        - `parse_cmd.py`: Module for parsing commands.
        - `readme_cmd.py`: Module for readme commands.
      - `context.py`: Module for context handling.
      - `main.py`: Main CLI module.
      - `utils.py`: Utility functions module.
    - `cli.py`: CLI entry point.
    - `core/`: Core functionality package.
      - `__init__.py`: Initialization file.
      - `docgen.py`: Document generation module.
      - `embedding.py`: Embedding module.
      - `parser.py`: Parsing module.
    - `utils/`: Utility functions package.
      - `__init__.py`: Initialization file.
      - `common.py`: Common utility functions.

Key Functions/Classes Summary:
- `LangDocContext` (class) in `context.py`
- `__init__` (function) in `context.py`
- `init_from_repo_path` (function) in `context.py`
- `cli` (function) in `main.py`
- `echo_styled` (function) in `utils.py`
- `get_parsed_files` (function) in `utils.py`
- `validate_api_key` (function) in `utils.py`
- `ask` (function) in `ask_cmd.py`
- `doc` (function) in `doc_cmd.py`
```

## Notable Classes/Functions

### `LangDocContext` (class) in `context.py`
- The `LangDocContext` class provides a central context for the langdoc project.
- It contains essential methods like `__init__` and `init_from_repo_path` for initializing and setting up the context.

### `cli` (function) in `main.py`
- The `cli` function in `main.py` serves as the entry point for the command-line interface of langdoc.
- It orchestrates the available commands and functionalities provided by the CLI.

### `echo_styled` (function) in `utils.py`
- The `echo_styled` function in `utils.py` is responsible for printing styled output to the console.
- It enhances the user experience by formatting and displaying information in a visually appealing way.

### `get_parsed_files` (function) in `utils.py`
- The `get_parsed_files` function in `utils.py` retrieves and processes parsed files for further analysis.
- It plays a crucial role in extracting relevant data for various operations within the project.

### `validate_api_key` (function) in `utils.py`
- The `validate_api_key` function in `utils.py` validates the API key used for authentication purposes.
- It ensures the security and integrity of interactions with external services.

### `ask` (function) in `ask_cmd.py`
- The `ask` function in `ask_cmd.py` implements the functionality for prompting user input and processing responses.
- It enables interactive communication with the user during specific operations.

### `doc` (function) in `doc_cmd.py`
- The `doc` function in `doc_cmd.py` handles the generation and documentation of project-related information.
- It facilitates the creation of documentation artifacts based on the provided input.

---

Feel free to expand on these classes and functions in more detail as needed for your project's documentation.

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
    langdoc parse --path /path/to/your/repo
    ```
-   **Generate documentation:**
    ```bash
    langdoc doc --path /path/to/your/repo --output-dir project_docs
    ```
-   **Ask questions about the code:**
    ```bash
    langdoc ask "How does the authentication work?" --path /path/to/your/repo
    ```
-   **Refresh this README:**
    ```bash
    langdoc readme --path /path/to/your/repo
    ```
