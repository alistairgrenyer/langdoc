"""
Specialized generator for code documentation.
"""
import os
from typing import Dict, Any, Optional, List

from langchain_core.prompts import ChatPromptTemplate
from . import Generator


class DocGenerator(Generator):
    """Specialized generator for creating code documentation."""
    
    def __init__(self, model_name="gpt-3.5-turbo", openai_api_key=None):
        """Initialize the DocGenerator.
        
        Args:
            model_name: Name of the LLM model to use, defaults to 'gpt-3.5-turbo'
            openai_api_key: API key for OpenAI, if None uses environment variable
        """
        super().__init__(model_name, openai_api_key)
        
        # Initialize prompt templates
        self.module_doc_prompt = ChatPromptTemplate.from_template("""
        Generate comprehensive markdown documentation for the following code.
        Format the documentation as markdown with proper sections, code blocks, and examples where relevant.
        
        Code to document:
        ```{language}
        {code_content}
        ```
        
        Module name: {module_name}
        
        Focus on:
        1. An overview of what the module does
        2. Main classes and functions with their purpose
        3. Usage examples
        4. Important notes or caveats
        
        Make the documentation clear, concise and well-structured.
        """)
        
        self.docstring_prompt = ChatPromptTemplate.from_template("""
        Generate Python docstrings in {style} format for the following code.
        The docstrings should be comprehensive but concise, explaining what the function/class does,
        parameters, return values, and any exceptions raised.
        
        Code to document:
        ```python
        {code_content}
        ```
        
        Return only the docstrings you would add or improve, in the exact format they should appear in the code.
        """)
    
    def generate_module_markdown(self, parsed_file: Dict[str, Any], output_dir: str = "docs") -> Optional[str]:
        """Generate markdown documentation for a module.
        
        Args:
            parsed_file: The parsed file data containing file_path, code, AST, etc.
            output_dir: Directory to save the generated markdown
            
        Returns:
            The path to the generated markdown file or None if generation failed
        """
        if not self.llm:
            print(f"Cannot generate documentation: LLM not initialized for {parsed_file['file_path']}")
            return None
            
        file_path = parsed_file["file_path"]
        file_name = os.path.basename(file_path)
        code_content = parsed_file.get("code", "")
        language = file_path.split(".")[-1] if "." in file_path else "txt"
        module_name = file_name.replace("." + language, "") if "." in file_name else file_name
        
        chain = self._create_chain(self.module_doc_prompt)
        if not chain:
            return None
            
        try:
            markdown_content = chain.invoke({
                "language": language,
                "code_content": code_content,
                "module_name": module_name
            })
            
            # Create output directory structure
            os.makedirs(output_dir, exist_ok=True)
            
            # Write markdown to file
            output_file = os.path.join(output_dir, f"{module_name}.md")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                
            return output_file
        except Exception as e:
            print(f"Error generating markdown for {file_path}: {e}")
            return None
            
    def update_file_with_docstrings(self, file_path: str, parsed_file: Dict[str, Any], 
                                  docstring_style: str = "Google") -> List[Dict[str, Any]]:
        """Generate docstring suggestions for a file.
        
        Args:
            file_path: Path to the file to update
            parsed_file: Parsed file data containing code, AST, etc.
            docstring_style: Style of docstrings to generate (Google, Numpy, etc.)
            
        Returns:
            A list of suggestions for docstring updates
        """
        if not self.llm:
            print(f"Cannot generate docstrings: LLM not initialized for {file_path}")
            return []
            
        code_content = parsed_file.get("code", "")
        
        chain = self._create_chain(self.docstring_prompt)
        if not chain:
            return []
            
        try:
            docstring_suggestions = chain.invoke({
                "style": docstring_style,
                "code_content": code_content
            })
            
            # Parse docstrings and prepare suggestions
            # This is where you'd implement actual file modification logic
            # For now, we're just returning the suggestions as text
            
            suggestions = [{
                "file_path": file_path,
                "suggested_docstrings": docstring_suggestions
            }]
            
            # Print the suggestions for now
            print(f"\nDocstring suggestions for {file_path}:")
            print(docstring_suggestions)
            
            return suggestions
        except Exception as e:
            print(f"Error generating docstrings for {file_path}: {e}")
            return []
