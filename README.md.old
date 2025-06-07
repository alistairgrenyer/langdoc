# LangDoc

Auto-generate high-quality documentation for codebases using LLMs and RAG.

LangDoc helps developers maintain comprehensive documentation by analyzing codebases and generating documentation that feels human-written—clear, concise, and representative of a mature project.

## Features

- **README Generation**: Create professional, human-like README files that accurately represent your project
- **RAG-powered Context**: Uses Retrieval Augmented Generation to embed and retrieve contextual information from your codebase
- **Clean Architecture**: Built following Clean Architecture principles with strict separation of concerns
- **Extensible Design**: Easily add new document generators through the plugin system

## Installation

```bash
pip install langdoc
```

For development:

```bash
git clone https://github.com/username/langdoc.git
cd langdoc
pip install -e ".[dev]"
```

## Usage

Generate a README for your project:

```bash
# Generate a README for the current directory
langdoc readme

# Generate a README for a specific project
langdoc readme --path /path/to/your/project

# Turn off RAG for faster generation (less context-aware)
langdoc readme --no-rag

# Specify a different OpenAI model
langdoc readme --model gpt-4
```

## Project Structure

LangDoc follows Clean Architecture principles with a strict src/ layout:

```
src/
├── langdoc/
    ├── cli/              # Command-line interface using Typer
    ├── application/      # Application use cases and services
    ├── domain/           # Business entities and interfaces
    └── infrastructure/   # External integrations (Git, LLMs, filesystem)
```

## Configuration

LangDoc requires an OpenAI API key:

- Set the `OPENAI_API_KEY` environment variable, or
- Use the `--api-key` CLI option

## Development

LangDoc follows these development practices:

- Code formatting with Black and isort
- Static type checking with mypy
- Testing with pytest (target: >90% coverage)
- Documentation with MkDocs and Google-style docstrings

## License

MIT
