# langdoc

## Project Summary

The `langdoc` project is a Python codebase designed to provide language documentation capabilities. It consists of the following key components:

- `LangDocContext` (class) in `context.py` for managing the context of language documentation
- `cli` (function) in `main.py` for command-line interface functionality
- `echo_styled` (function) in `utils.py` for styled output in the CLI
- `get_parsed_files` (function) in `utils.py` for parsing files
- `validate_api_key` (function) in `utils.py` for validating API keys
- `ask` (function) in `ask_cmd.py` for asking questions
- `doc` (function) in `doc_cmd.py` for documentation purposes

The project structure includes directories such as `cli`, `core`, and `utils`, each containing relevant Python files for different functionalities. The `langdoc` project aims to streamline the process of language documentation through its CLI and core functionalities.

## File Structure

```
langdoc/
├── .langdoc_db/
│   └── langdoc_acf8549fe385693015732ed0b79468cd/
│       └── 73a42ec6-e8a4-4e6e-a2aa-ccf5bcc61242/
├── langdoc/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── commands/
│   │   │         └── ... (too deep)
│   │   ├── context.py
│   │   ├── main.py
│   │   └── utils.py
│   ├── cli.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── docgen.py
│   │   ├── embedding.py
│   │   └── parser.py
│   └── utils/
│       ├── __init__.py
│       └── common.py
├── langdoc.egg-info/
└── setup.py
```

The `langdoc` project is structured as follows:

- The `.langdoc_db` directory contains internal database files for the project.
- The `langdoc` directory is the main package containing the following modules:
  - `cli`: Contains command-line interface related files.
  - `core`: Contains core functionality modules like document generation, embedding, and parsing.
  - `utils`: Contains utility functions used throughout the project.

Key files include `context.py`, `main.py`, `utils.py`, `docgen.py`, `embedding.py`, `parser.py`, and `common.py`.

The project also includes `langdoc.egg-info` and `setup.py` for packaging and distribution purposes.

## Notable Classes/Functions

### Classes:
- `LangDocContext` (in `context.py`): Class responsible for managing the context of the LangDoc application.

### Functions:
- `__init__` (in `context.py`): Function to initialize the LangDocContext class.
- `init_from_repo_path` (in `context.py`): Function to initialize the context from a repository path.
- `cli` (in `main.py`): Function to handle the command-line interface of LangDoc.
- `echo_styled` (in `utils.py`): Function to echo styled output to the console.
- `get_parsed_files` (in `utils.py`): Function to retrieve parsed files.
- `validate_api_key` (in `utils.py`): Function to validate an API key.
- `ask` (in `ask_cmd.py`): Function to prompt the user for input.
- `doc` (in `doc_cmd.py`): Function to handle documentation commands.

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
