"""
Specialized generator for README.md file creation.
"""
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from . import Generator

class ReadmeGenerator(Generator):
    """Specialized generator for creating README.md files."""
    
    def __init__(self, model_name="gpt-3.5-turbo", openai_api_key=None):
        """Initialize the ReadmeGenerator.
        
        Args:
            model_name: OpenAI model to use, defaults to 'gpt-3.5-turbo'
            openai_api_key: Optional API key, uses env var if not provided
        """
        super().__init__(model_name, openai_api_key)
        
        # Define README section templates
        self.section_prompt = self._create_section_prompt()
        self.section_chain = self._create_chain(self.section_prompt) if self.llm else None
    
    def _create_section_prompt(self):
        """Create the prompt template for generating README sections."""
        return ChatPromptTemplate.from_template(
            """You are an expert technical documentation writer tasked with creating a 
            comprehensive README.md section for a codebase.
            
            Given the following information, craft a high-quality '{section_title}' section for a README.md file:  
            
            Project Name: {project_name}
            
            File Structure Overview:
            {file_structure}
            
            Key Functions/Classes Summary:
            {key_elements_summary}
            
            File Descriptions:
            {file_descriptions}
            
            Context-Specific Instructions:
            {context}
            
            INSTRUCTIONS:
            1. Create a well-structured '{section_title}' section for a README.md file
            2. Use clear and concise language with proper Markdown formatting
            3. Include important details from the provided information as appropriate
            4. Focus on explaining the purpose, functionality, and structure as needed for this section
            5. Format your response as Markdown with appropriate headers, formatting, and sections
            """
        )
    
    def generate_section(self, section_title: str, project_name: str, file_structure: str, 
                        key_elements_summary: str, file_descriptions: str = "", context: str = "") -> Optional[str]:
        """Generate a single section of a README document.
        
        Args:
            section_title: Title of the section (e.g., "Project Summary")
            project_name: Name of the project
            file_structure: Markdown representation of file tree
            key_elements_summary: Summary of important functions and classes
            file_descriptions: RAG-generated descriptions of key files
            context: Additional instructions for this specific section
            
        Returns:
            Generated markdown content for the section, or None if generation failed
        """
        if not self.section_chain:
            return None
        
        try:
            content = self.section_chain.invoke({
                "section_title": section_title,
                "project_name": project_name,
                "file_structure": file_structure,
                "key_elements_summary": key_elements_summary,
                "file_descriptions": file_descriptions,
                "context": context or ""
            })
            return content
        except Exception as e:
            print(f"Error generating README section '{section_title}': {e}")
            return None
    
    def generate_readme(self, project_name: str, file_structure: str, 
                       key_elements_summary: str, file_descriptions: str) -> Optional[str]:
        """Generate a complete README.md file with all standard sections.
        
        Args:
            project_name: Name of the project
            file_structure: Markdown representation of file tree
            key_elements_summary: Summary of important functions and classes 
            file_descriptions: RAG-generated descriptions of key files
            
        Returns:
            Complete README.md content as a string, or None if generation failed
        """
        if not self.llm:
            print("Cannot generate README: LLM not available.")
            return None
            
        # Start with the project title
        readme_content = f"# {project_name}\n\n"
        
        # Generate Project Summary section
        project_summary = self.generate_section(
            "Project Summary",
            project_name,
            file_structure,
            "",  # No need for key elements in summary
            file_descriptions,
            context="Create a concise project summary that explains what the project does and its main benefits. "
                  "Keep this section brief (2-3 paragraphs max) but informative, focusing on the project's purpose, "
                  "primary features, and intended use cases."
        )
        if project_summary:
            readme_content += f"{project_summary}\n\n" 
        else:
            readme_content += f"## Project Summary\n\nA tool for {project_name} that helps with code documentation.\n\n"

        # Generate File Structure section
        file_structure_content = self.generate_section(
            "File Structure",
            project_name,
            file_structure,
            key_elements_summary,
            file_descriptions,
            context="Explain the organization of files and directories in the project. Focus on the main components and "
                  "their relationships."
        )
        if file_structure_content:
            readme_content += f"{file_structure_content}\n\n"
        else:
            readme_content += f"## File Structure\n\n```\n{file_structure}\n```\n\n"

        # Generate Core Features section
        core_features_content = self.generate_section(
            "Core Features",
            project_name,
            file_structure,
            key_elements_summary,
            file_descriptions,
            context="Focus on the main capabilities and features of the tool rather than listing functions/classes. "
                  "Explain what the tool allows users to do, how it can be useful, and what problems it solves."
        )
        if core_features_content:
            readme_content += f"{core_features_content}\n\n"
        else:
            readme_content += "## Core Features\n\nThis tool offers features for parsing code, generating documentation, and answering questions about codebases.\n\n"

        # Add Setup and Usage section
        setup_instructions = """### Installation

1.  Install from PyPI:
    ```bash
    pip install langdoc
    ```

2. Set up OpenAI API key as an environment variable:
   ```bash
   # On Linux/Mac
   export OPENAI_API_KEY="your-api-key-here"
   
   # On Windows
   set OPENAI_API_KEY=your-api-key-here
   ```
   
   Alternatively, create a `.env` file in your project directory:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
"""
        
        quick_start_guide = """### Quick Start Guide

1. **Parse your repository and build embeddings (required first step):**
   ```bash
   langdoc parse
   ```
   This analyzes your code and creates embeddings for semantic search capabilities.

2. **Generate documentation for your project:**
   ```bash
   langdoc doc --output-dir docs
   ```

3. **Ask questions about your codebase:**
   ```bash
   langdoc ask "How does the authentication work?"
   ```
   Get answers based on the semantic understanding of your code.

4. **Generate a descriptive README:**
   ```bash
   langdoc readme
   ```
   Creates or updates a README.md file with project information.

All commands accept a `--path` option to specify a different repository path. By default, langdoc works in the current directory.
"""
        
        # Try to generate a custom usage section, fall back to template if it fails
        usage_section = self.generate_section(
            "Setup and Usage",
            project_name,
            file_structure,
            key_elements_summary,
            file_descriptions,
            context="Provide clear installation instructions and quick start guide for using the tool. Focus on how "
                   "to install via pip and how to use the basic commands."
        )
        
        if usage_section:
            readme_content += f"{usage_section}\n\n"
        else:
            readme_content += f"## Setup and Usage\n\n{setup_instructions}\n\n{quick_start_guide}\n\n"
        
        return readme_content
        
    def generate_file_description(self, code_snippet: str, file_name: str) -> str:
        """Generate a brief description of a file based on its content.
        
        Args:
            code_snippet: The content or snippet of code from the file
            file_name: The name of the file
            
        Returns:
            A brief description of the file's purpose and functionality
        """
        if not self.llm:
            return f"No description available for {file_name}"
            
        # Create a prompt template for file descriptions
        file_desc_prompt = ChatPromptTemplate.from_template(
            """Analyze the following code from a file named '{file_name}' and provide a concise description:

            ```
            {code_snippet}
            ```
            
            Provide a brief (2-3 sentences) technical description of what this file does, 
            focusing on its purpose and main functionality. Be concise and specific.
            """
        )
        
        chain = self._create_chain(file_desc_prompt)
        try:
            return chain.invoke({
                "file_name": file_name,
                "code_snippet": code_snippet[:2000]  # Limit to avoid token overflow
            })
        except Exception as e:
            print(f"Error generating description for {file_name}: {e}")
            return f"File: {file_name} (description generation failed)"
