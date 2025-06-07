"""Integration tests for the CLI interface."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from src.langdoc.cli.app import app


@pytest.fixture
def runner():
    """Fixture for a Typer CLI test runner."""
    return CliRunner()


@pytest.mark.parametrize(
    "args",
    [
        [],  # No args should show help
        ["--help"],  # Help flag
        ["readme", "--help"],  # Command help
    ],
)
def test_cli_help(runner, args):
    """Test that the CLI help works."""
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_version_command(runner):
    """Test the version command."""
    with patch("langdoc.__version__", "0.1.0"):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout


@patch("langdoc.cli.app.IndexCodebaseCommand")
@patch("langdoc.cli.app.GenerateReadmeCommand")
@patch("langdoc.cli.app.os.environ", {"OPENAI_API_KEY": "fake-key"})
def test_readme_command_execution(
    mock_generate_command, mock_index_command, runner, tmp_path
):
    """Test that the readme command executes the right command classes."""
    # Configure mocks
    mock_index_instance = mock_index_command.return_value
    mock_generate_instance = mock_generate_command.return_value
    mock_generate_instance.execute.return_value = tmp_path / "README.md"

    # Run the command
    result = runner.invoke(
        app, ["readme", "--rag", str(tmp_path), "-o", str(tmp_path)]
    )

    # Check command executed successfully
    assert result.exit_code == 0

    # Verify command classes were instantiated and executed
    mock_index_command.assert_called_once()
    mock_generate_command.assert_called_once()
    mock_index_instance.execute.assert_called_once()
    mock_generate_instance.execute.assert_called_once()


@patch("langdoc.cli.app.CodeVectorStore")
@patch("langdoc.cli.app.ReadmeGenerationLLMService")
@patch("langdoc.cli.app.os.environ", {})
def test_readme_command_fails_without_api_key(
    mock_llm_service, mock_vector_store, runner, tmp_path
):
    """Test that the readme command fails without an API key."""
    # Run the command without OPENAI_API_KEY in environment and without --api-key
    result = runner.invoke(app, ["readme", str(tmp_path)])

    # Check command failed
    assert result.exit_code == 1
    assert "No OpenAI API key provided" in result.stdout
