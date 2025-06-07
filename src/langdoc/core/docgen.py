"""
Documentation generation module for creating and enhancing documentation with LLMs.
"""
import os
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found for docgen. LLM features will be disabled.")


class DocGenerator:
    def __init__(self, model_name="gpt-3.5-turbo"):
        """Initialize the DocGenerator with specified LLM model.
        
        Args:
            model_name: Name of the LLM model to use, defaults to 'gpt-3.5-turbo'
        """
        if OPENAI_API_KEY:
            self.llm = ChatOpenAI(model=model_name, openai_api_key=OPENAI_API_KEY, temperature=0.2)
            self.output_parser = StrOutputParser()
            self.docstring_prompt = ChatPromptTemplate.from_template(
                """Analyze the following {code_type} named '{code_name}' and generate a professional docstring for it.

                ```python
                {code_content}
                ```
                
                INSTRUCTIONS:
                1. Create a clear, concise, and informative docstring that follows PEP 257 standards
                2. Document the {code_type}'s purpose, functionality, and behavior
                3. For functions/methods: document parameters, return values, raised exceptions, and usage examples when appropriate
                4. For classes: document behavior, key methods, attributes, and usage patterns
                5. Use the appropriate docstring style (triple quotes)
                6. Focus on technical accuracy and completeness
                7. If code has type hints, ensure docstring aligns with them
                
                The existing docstring is: '{existing_docstring}'
                
                If the existing docstring is already adequate (covers purpose, parameters, returns values as needed), respond with 'SKIP'.
                Otherwise, provide ONLY the new docstring text without any additional explanation or markdown formatting.
                """
            )
            self.module_summary_prompt = ChatPromptTemplate.from_template(
                """Generate a comprehensive module documentation in markdown format for a Python module located at '{file_path}'.
                
                The module contains the following functions and classes: 
                {definitions_summary}
                
                INSTRUCTIONS:
                1. Create a well-structured markdown document that explains the module's purpose, functionality, and organization
                2. Start with a clear module overview explaining what problem it solves
                3. Document the main components (classes, functions) with their relationships and dependencies
                4. Highlight key usage patterns and examples where appropriate
                5. Use proper markdown formatting with headers, lists, code blocks, and emphasis
                6. Make the documentation useful for both new and experienced developers
                7. Focus on explaining the module's role within the larger project context
                
                Respond with a professional markdown document, structured with appropriate headings and sections.
                """
            )
            self.readme_section_prompt = ChatPromptTemplate.from_template(
                """You are an expert technical documentation writer tasked with creating a comprehensive README.md section for a codebase.
                
                Given the following information, craft a high-quality '{section_title}' section for a README.md file:  
                
                Project Name: {project_name}
                
                File Structure Overview:
{file_structure}

                
                Key Functions/Classes Summary:
{key_elements_summary}

                
                File Descriptions:
{file_descriptions}

                
                Existing Section Content (if updating):
{existing_section_content}

                Context-Specific Instructions:
{context}
                
                INSTRUCTIONS:
                1. Create a well-structured '{section_title}' section for a README.md file
                2. Use clear and concise language with proper Markdown formatting
                3. Include important details from the provided information as appropriate
                4. If 'existing_section_content' is provided, use it as a basis, but enhance and update it
                5. Focus on explaining the purpose, functionality, and structure as needed for this section
                6. Format your response as Markdown with appropriate headers, formatting, and sections
                7. If updating an existing section, preserve the general structure but improve content
                8. If the existing content is already excellent and complete, you may respond with 'No change needed'
                9. Follow any specific guidance provided in the Context-Specific Instructions
                
                For this '{section_title}' section, focus specifically on providing:
                - Clear explanations relevant to the section topic
                - Well-organized structure with proper headings
                - Code examples or formatting as appropriate
                - Connections to other parts of the project where relevant
                
                Respond with ONLY the formatted section content in Markdown, ready to be directly inserted into the README.md file.
                Do NOT include any explanation outside of the content itself.
                """
            )
            
            self.file_description_prompt = ChatPromptTemplate.from_template(
                """Based on the following code snippet, provide a brief 1-2 sentence description of what the file '{file_name}' does.
                
                Code snippet:
                ```
                {code_snippet}
                ```
                
                Focus on the file's main purpose and functionality. Be concise and technical.
                Respond with ONLY the description, no additional text or formatting.
                """
            )
            # Output parser for consistent handling of results
            self.output_parser = StrOutputParser()
        else:
            self.llm = None
            print("DocGenerator initialized without LLM. Documentation generation will be unavailable.")

    def generate_docstring(self, code_type: str, code_name: str, code_content: str, 
                         existing_docstring: Optional[str] = None) -> Optional[str]:
        """Generate a docstring for the provided code.
        
        Args:
            code_type: Type of code entity ('function', 'class', etc.)
            code_name: Name of the code entity
            code_content: Full content of the code entity
            existing_docstring: Existing docstring if any
            
        Returns:
            Generated docstring or None if generation failed
        """
        if not self.llm:
            return None
            
        # Use empty string if no docstring exists
        if existing_docstring is None:
            existing_docstring = ""
        
        chain = self.docstring_prompt | self.llm | self.output_parser
        
        try:
            result = chain.invoke({"code_type": code_type, "code_name": code_name, 
                                "code_content": code_content, "existing_docstring": existing_docstring})
            return None if result == "SKIP" else result
        except Exception as e:
            print(f"Error generating docstring for {code_name}: {e}")
            return None
    
    def update_file_with_docstrings(self, file_path: str, parsed_data: Dict[str, Any]) -> None:
        """Updates a Python file with generated docstrings for functions/classes if they are missing or inadequate.
        
        Args:
            file_path: Path to the Python file
            parsed_data: Parsed data from the file containing AST information
        """
        if not self.llm:
            print("Cannot update docstrings: LLM not available.")
            return
        
        print(f"\nAnalyzing docstrings for {file_path}...")
        
        # Process each definition in the parsed data
        for definition in parsed_data.get('definitions', []):
            def_type = definition.get('type', '')
            def_name = definition.get('name', '')
            code_content = definition.get('content', '')
            existing_docstring = definition.get('docstring', '')
            
            print(f"  Checking {def_type} '{def_name}'...")
            
            # Don't generate docstrings for simple properties, getters, setters
            if def_type == 'method' and (def_name.startswith('__') and def_name.endswith('__')):
                print(f"    Skipping special method {def_name}")
                continue
                
            if code_content:
                docstring = self.generate_docstring(def_type, def_name, code_content, existing_docstring)
                if docstring and docstring != "SKIP":
                    # For now, just print suggestions; actually modifying source code requires careful handling
                    print(f"    Suggested docstring for {def_name}:")
                    print(f"    {docstring}\n")
                else:
                    print(f"    No changes needed for {def_name}")
            
            # Process nested definitions (methods in classes)
            for nested_def in definition.get('children', []):
                nested_type = nested_def.get('type', '')
                nested_name = nested_def.get('name', '')
                nested_content = nested_def.get('content', '')
                nested_docstring = nested_def.get('docstring', '')
                
                print(f"    Checking {nested_type} '{nested_name}'...")
                
                if nested_content:
                    docstring = self.generate_docstring(nested_type, nested_name, nested_content, nested_docstring)
                    if docstring and docstring != "SKIP":
                        print(f"      Suggested docstring for {nested_name}:")
                        print(f"      {docstring}\n")
                    else:
                        print(f"      No changes needed for {nested_name}")
                        
    def generate_module_markdown(self, parsed_file_data: Dict[str, Any], output_dir: str = 'docs') -> Optional[str]:
        """Generates a markdown file summarizing a module.
        
        Args:
            parsed_file_data: Dictionary containing parsed information about the module
            output_dir: Directory to save the generated markdown file
            
        Returns:
            Path to the generated markdown file if successful, None otherwise
        """
        if not self.llm:
            print("Cannot generate module markdown: LLM not available.")
            return None
            
        file_path = parsed_file_data.get('file_path', '')
        if not file_path:
            print("Error: No file path provided for markdown generation.")
            return None
            
        # Create a summary of the module's definitions
        definitions = parsed_file_data.get('definitions', [])
        if not definitions:
            print(f"No definitions found in {file_path}. Skipping markdown generation.")
            return None
            
        definitions_summary = []
        for defn in definitions:
            def_type = defn.get('type', '')
            def_name = defn.get('name', '')
            docstring = defn.get('docstring', '')
            docstring_summary = f"{docstring[:100]}..." if len(docstring) > 100 else docstring
            
            definitions_summary.append(f"* {def_type.capitalize()} `{def_name}`: {docstring_summary}")
            
            # Include info about methods for classes
            if def_type == 'class':
                for method in defn.get('children', []):
                    method_name = method.get('name', '')
                    method_docstring = method.get('docstring', '')
                    method_summary = f"{method_docstring[:50]}..." if len(method_docstring) > 50 else method_docstring
                    definitions_summary.append(f"  * Method `{method_name}`: {method_summary}")
        
        definitions_summary_text = "\n".join(definitions_summary)
        
        # Generate the markdown content
        chain = self.module_summary_prompt | self.llm | self.output_parser
        try:
            markdown_content = chain.invoke({
                "file_path": file_path,
                "definitions_summary": definitions_summary_text
            })
            
            # Create output directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Determine the output file path
            file_name = os.path.basename(file_path).replace('.py', '.md')
            output_path = os.path.join(output_dir, file_name)
            
            # Write the markdown content to the file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
                
            print(f"✅ Generated markdown documentation for {file_name} at {output_path}")
            return output_path
        except Exception as e:
            print(f"Error generating markdown for {file_path}: {e}")
            return None
    
    def generate_readme_section(self, section_title: str, project_name: str, file_structure: str, 
                              key_elements_summary: str, file_descriptions: str = "No detailed file descriptions available.",
                              existing_section_content: str = "", context: str = "") -> Optional[str]:
        """Generate a well-structured README section using the available project information.
        
        Args:
            section_title: The title for the section (e.g., "Project Summary")
            project_name: The name of the project
            file_structure: Markdown representation of the file structure
            key_elements_summary: Summary of key functions and classes
            file_descriptions: Detailed descriptions of files obtained via RAG
            existing_section_content: Existing content for this section (if any)
            context: Additional context-specific instructions for this section
            
        Returns:
            Generated markdown content for the section, or None if generation failed
        """
        if not self.llm:
            print(f"Cannot generate README section '{section_title}': LLM not available.")
            return None
        
        chain = self.readme_section_prompt | self.llm | self.output_parser
        try:
            content = chain.invoke({
                "section_title": section_title,
                "project_name": project_name,
                "file_structure": file_structure,
                "key_elements_summary": key_elements_summary,
                "file_descriptions": file_descriptions,
                "existing_section_content": existing_section_content,
                "context": context or ""
            })
            return content
        except Exception as e:
            print(f"Error generating README section '{section_title}': {e}")
            return None
    
    def generate_readme(self, project_name: str, file_structure: str, key_elements_summary: str, 
                   file_descriptions: str, repo_path: str) -> Optional[str]:
        """Generate a complete README document for a project.
        
        This method handles the entire README generation process, including all sections:
        - Project Summary
        - File Structure
        - Core Features
        - Setup and Installation
        - Quick Start Guide
        
        Args:
            project_name: The name of the project
            file_structure: Markdown representation of the file structure
            key_elements_summary: Summary of key functions and classes
            file_descriptions: Detailed descriptions of files obtained via RAG
            repo_path: Path to the repository (for checking presence of files like requirements.txt)
        
        Returns:
            Complete README markdown content, or None if generation failed
        """
        if not self.llm:
            print("Cannot generate README: LLM not available.")
            return None
        
        # Begin README content generation
        readme_content = f"# {project_name}\n\n"
        
        # Project Summary Section
        project_summary = self.generate_readme_section(
            "Project Summary", 
            project_name, 
            file_structure, 
            "",  # No need to include key elements in summary
            file_descriptions,
            context="Create a concise project summary that explains what the project does and its main benefits. "
                   "Keep this section brief (2-3 paragraphs max) but informative, focusing on the project's purpose, "
                   "primary features, and intended use cases. Avoid overly technical language and write for a "
                   "developer audience who needs to understand if this tool is relevant to their needs."
        )
        if project_summary and project_summary.lower().strip() != 'no change needed':
            readme_content += f"{project_summary}\n\n"
        else:
            readme_content += f"## Project Summary\n\nA tool for {project_name} that helps with code documentation.\n\n"

        # File Structure Section
        file_structure_content = self.generate_readme_section(
            "File Structure",
            project_name,
            file_structure,
            key_elements_summary,
            file_descriptions,
            context="Explain the organization of files and directories in the project. Focus on the main components and "
                   "their relationships. You can use your judgment to organize the structure in a way that's most "
                   "helpful to new users of the project."
        )
        if file_structure_content and file_structure_content.lower().strip() != 'no change needed':
            readme_content += f"{file_structure_content}\n\n"
        else:
            readme_content += f"## File Structure\n\n```\n{file_structure}\n```\n\n"

        # Core Features Section
        core_features_content = self.generate_readme_section(
            "Core Features",
            project_name,
            file_structure,
            key_elements_summary,
            file_descriptions,
            context="Focus on the main capabilities and features of the tool rather than listing functions/classes. "
                   "Explain what the tool allows users to do, how it can be useful, and what problems it solves. "
                   "Organize by functionality, not by code structure."
        )
        if core_features_content and core_features_content.lower().strip() != 'no change needed':
            readme_content += f"{core_features_content}\n\n"
        else:
            readme_content += "## Core Features\n\nThis tool offers features for parsing code, generating documentation, and answering questions about codebases.\n\n"

        # Setup and Usage Section
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
        
        # Add Setup and Usage section
        usage_section = self.generate_readme_section(
            "Setup and Usage",
            project_name,
            file_structure,
            key_elements_summary,
            file_descriptions,
            context="Provide clear installation instructions and quick start guide for using the tool. Focus on how "
                   "to install via pip and how to use the basic commands. Make sure the instructions are practical "
                   "and concise."
        )
        
        if usage_section and usage_section.lower().strip() != 'no change needed':
            readme_content += f"{usage_section}\n\n"
        else:
            readme_content += f"## Setup and Usage\n\n{setup_instructions}\n\n{quick_start_guide}\n\n"
        
        return readme_content
    
    def generate_file_description(self, code_snippet: str, file_name: str) -> str:
        """Generate a brief description of a file based on a code snippet.
        
        Args:
            code_snippet: A representative code snippet from the file
            file_name: The name of the file to describe
            
        Returns:
            A brief description of the file or a default message if generation fails
        """
        if not self.llm:
            return "No description available (LLM not configured)"
            
        chain = self.file_description_prompt | self.llm | self.output_parser
        try:
            return chain.invoke({
                "file_name": file_name,
                "code_snippet": code_snippet
            })
        except Exception as e:
            print(f"Error generating file description for {file_name}: {e}")
            return "No description available (error during generation)"
            
    def generate_with_rag(self, query: str, retrieved_docs: list, context_instruction: str) -> Optional[str]:
        """Generate content using RAG (Retrieval Augmented Generation) approach.
        
        Args:
            query: The query to answer
            retrieved_docs: List of document objects retrieved from vector store
            context_instruction: Instructions on how to use the retrieved documents
            
        Returns:
            Generated content based on the retrieved documents, or None if generation failed
        """
        if not self.llm:
            print("Cannot generate with RAG: LLM not available.")
            return None
        
        # Create RAG prompt template
        rag_prompt = ChatPromptTemplate.from_template(
            """You are a technical documentation expert focused on explaining code structure and functionality.
            
            Based on the following retrieved code chunks, respond to this query:
            {query}
            
            {context_instruction}
            
            Retrieved code chunks:
            {chunks}
            
            Focus on being accurate, comprehensive, and clear in your response.
            Format your response in clean markdown that can be directly incorporated into documentation.
            """
        )
        
        # Process retrieved documents
        if not retrieved_docs or len(retrieved_docs) == 0:
            return "No relevant code context was found to answer this query."
        
        # Extract content from retrieved documents
        chunks_text = []
        for i, doc in enumerate(retrieved_docs):
            source = doc.metadata.get("source", "Unknown source")
            file_path = doc.metadata.get("file_path", "Unknown file")
            chunks_text.append(f"Chunk {i+1} from {source or file_path}:\n```python\n{doc.page_content}\n```\n")
        
        chunks_combined = "\n".join(chunks_text)
        
        # Create and run the chain
        chain = rag_prompt | self.llm | self.output_parser
        try:
            result = chain.invoke({
                "query": query,
                "context_instruction": context_instruction,
                "chunks": chunks_combined
            })
            return result
        except Exception as e:
            print(f"Error generating RAG content: {e}")
            return None
