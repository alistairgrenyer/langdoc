# langdoc

Welcome to langdoc, a tool that automates the generation of documentation for codebases using Language Model Models (LLMs) and Retrieval-Augmented Generation (RAG).

## Installation

To install langdoc, simply clone the repository from [here](https://github.com/alistairgrenyer/langdoc) and navigate to the project directory.

```bash
git clone https://github.com/alistairgrenyer/langdoc.git
cd langdoc
```

Install the required dependencies by running:

```bash
pip install -r requirements.txt
```

## Usage

langdoc can be used to automatically generate documentation for codebases. Simply run the following command:

```langdoc readme
```

This will trigger the documentation generation process using LLMs and RAG.

## Project Structure

- `src/`: Contains the source code of the langdoc project.
  - `src/langdoc/`: Main package for langdoc.
  - `src/langdoc/application/`: Contains application logic.
    - `src/langdoc/application/codebase_analysis_service.py`: Module for analyzing codebases.
    - `src/langdoc/application/documentation_generator_service.py`: Module for generating documentation.
    - `src/langdoc/application/__init__.py`
    - ... (and 20 more items)
- `tests/`: Contains test cases for the langdoc project.
  - `tests/conftest.py`
  - `tests/integration/`: Integration test cases.
    - `tests/integration/test_cli.py`
  - `tests/unit/`: Unit test cases.
    - `tests/unit/test_codebase_analysis.py`
    - ... (and 1 more item)
- `docs/`: Contains Architecture Decision Records (ADRs).
- `root_files/`: Contains project configuration files.
  - `pyproject.toml`
  - `requirements.txt`

## Contributing

If you would like to contribute to langdoc, please check out the [Contribution Guidelines](CONTRIBUTING.md).

## License

This project is licensed under the terms of the [MIT License](LICENSE).