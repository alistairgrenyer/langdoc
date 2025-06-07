"""Specialized LLM service for README generation."""

from typing import Dict, List, Optional

from langdoc.infrastructure.llm.base_llm_service import LLMDocumentationService


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
        context: Optional[List[Dict[str, str]]] = None,
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
