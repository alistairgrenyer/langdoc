"""LLM service implementation."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import rich.console
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.schema.messages import SystemMessage

from langdoc.domain.interfaces import LLMService


class LLMDocumentationService(LLMService):
    """Implementation of LLM service for generating documentation."""

    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.2,
        streaming: bool = True,
        api_key: Optional[str] = None,
        console: Optional[rich.console.Console] = None,
    ):
        """Initialize the LLM documentation service.

        Args:
            model_name: Name of the LLM model to use
            temperature: Model temperature parameter
            streaming: Whether to stream output
            api_key: OpenAI API key
            console: Optional Rich console for output
        """
        self.console = console or rich.console.Console()
        
        # Get API key
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
            
        if not api_key:
            self.console.print(
                "[yellow]Warning: No OpenAI API key provided. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter.[/yellow]"
            )
            
        # Setup callbacks for streaming
        callbacks = None
        if streaming:
            callbacks = CallbackManager([StreamingStdOutCallbackHandler()])
            
        # Initialize chat model
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=api_key,
            streaming=streaming,
            callback_manager=callbacks if streaming else None,
            verbose=True
        )

    def generate_text(
        self, prompt: str, context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate text using an LLM.

        Args:
            prompt: The prompt to send to the LLM
            context: Optional context to include with the prompt

        Returns:
            Generated text from the LLM
        """
        system_message = self._create_system_prompt(context)
        
        # Create chat prompt template
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_message),
                HumanMessagePromptTemplate.from_template("{prompt}")
            ]
        )
        
        # Format prompt with input variables
        formatted_prompt = chat_prompt.format_prompt(prompt=prompt)
        
        # Generate response
        response = self.llm(formatted_prompt.to_messages())
        return response.content

    def _create_system_prompt(self, context: Optional[List[Dict[str, str]]] = None) -> str:
        """Create a system prompt with optional context.

        Args:
            context: Optional context information to include in the prompt

        Returns:
            System prompt string
        """
        base_prompt = (
            "You are a documentation expert specialized in creating high-quality "
            "documentation for software projects. You excel at writing clear, "
            "concise, and comprehensive documentation that follows best practices."
        )
        
        if not context:
            return base_prompt
            
        context_text = ""
        for doc in context:
            source = doc.get("source", "unknown")
            content = doc.get("content", "")
            if content:
                context_text += f"\n\nFILE: {source}\n```\n{content}\n```\n"
                
        system_prompt = (
            f"{base_prompt}\n\n"
            f"Below is context information from the codebase. Use this context to inform "
            f"your documentation generation, but do not directly copy large sections of code.\n"
            f"{context_text}\n\n"
            f"Generate documentation that is clear, concise, and follows best practices. "
            f"The documentation should feel like it was written by a human - conversational "
            f"yet professional - and accurately reflect the codebase structure and functionality."
        )
        
        return system_prompt


class ReadmeGenerationLLMService(LLMDocumentationService):
    """Specialized LLM service for generating README files."""

    def generate_readme(
        self, 
        project_name: str,
        project_description: Optional[str], 
        project_structure: Dict[str, List[str]],
        has_cli: bool,
        cli_commands: Optional[Dict[str, str]],
        dependencies: Optional[List[str]],
        git_info: Dict[str, str],
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate a README.md file for a project.

        Args:
            project_name: Name of the project
            project_description: Optional project description
            project_structure: Dictionary representing project structure
            has_cli: Whether the project has a CLI
            cli_commands: Optional dictionary of CLI commands and descriptions
            dependencies: Optional list of project dependencies
            git_info: Git repository information
            context: Optional context from vector store

        Returns:
            Generated README content
        """
        # Create project structure string
        structure_str = ""
        for dir_name, contents in project_structure.items():
            structure_str += f"\n- {dir_name}/"
            # Only show a few items per directory to avoid overloading
            for item in contents[:5]:
                structure_str += f"\n  - {item}"
            if len(contents) > 5:
                structure_str += f"\n  - ... ({len(contents) - 5} more items)"
                
        # Create dependencies string
        deps_str = ""
        if dependencies:
            deps_str = "\n".join([f"- {dep}" for dep in dependencies[:10]])
            if len(dependencies) > 10:
                deps_str += f"\n- ... ({len(dependencies) - 10} more dependencies)"
                
        # Create CLI commands string
        cli_str = ""
        if has_cli and cli_commands:
            for cmd, desc in cli_commands.items():
                cli_str += f"\n- `{cmd}`: {desc}"
                
        # Determine repository information
        repo_info = ""
        if git_info.get("is_git_repo") == "true":
            remote_url = git_info.get("remote_url", "")
            if "github.com" in remote_url:
                repo_owner = git_info.get("repo_owner", "")
                repo_name = git_info.get("repo_name", project_name)
                repo_info = f"\nRepository: https://github.com/{repo_owner}/{repo_name}"
                
        # Create prompt for README generation
        prompt = f"""
        Generate a professional README.md file for the following project:

        Project Name: {project_name}
        Description: {project_description or 'A Python project using Clean Architecture'}
        {repo_info}

        Project Structure:
        {structure_str}

        {"Dependencies:" if deps_str else ""}
        {deps_str}

        {"CLI Commands:" if cli_str else ""}
        {cli_str}

        The README should feel human-written - clear, concise, and representative of a mature, well-structured open-source project.
        It should naturally reflect the project's purpose, structure, and usage without enforcing a strict format.
        
        Include sections for:
        1. Introduction/Overview
        2. Installation
        3. Usage (including CLI usage if applicable)
        4. Project Structure
        5. Contributing (if applicable)
        6. License (if a license file exists)
        
        Make sure the README is written in a professional but approachable tone.
        Format the README using standard Markdown.
        """

        return self.generate_text(prompt, context)
