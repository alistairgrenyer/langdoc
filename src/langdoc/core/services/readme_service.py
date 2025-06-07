"""
README generation service using RAG.
Separates README generation concerns from the CLI command.
"""
import os
import logging
from typing import Dict, Any, List, Optional, Union, Protocol

from langdoc.core.generators.readme import ReadmeGenerator
from langdoc.utils.common import get_file_tree

logger = logging.getLogger("langdoc.readme")


class FileDescriptionGenerator(Protocol):
    """Protocol defining the required interface for file description generators."""
    
    def generate_file_description(self, code_snippet: str, file_name: str) -> str:
        """Generate a description for a file based on its content."""
        ...
        
    def generate_readme(self, project_name: str, file_structure: str, 
                      key_elements_summary: str, file_descriptions: str) -> Optional[str]:
        """Generate a README file content."""
        ...

class ReadmeService:
    """Service for generating README files using RAG.
    
    This service orchestrates README generation by coordinating project information,
    file descriptions, and document structure generation.
    """
    
    def __init__(self, generator: Optional[FileDescriptionGenerator] = None, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize the README service with a generator.
        
        Args:
            generator: A generator instance that implements FileDescriptionGenerator protocol.
                      If None, a new ReadmeGenerator will be created.
            model_name: The LLM model to use if a new generator needs to be created
        """
        self.generator = generator or ReadmeGenerator(model_name=model_name)
        self.logger = logger
        
    def process_file_descriptions(self, file_data: List[Dict[str, str]]) -> str:
        """
        Process file data from RAG results into a formatted description string.
        
        Args:
            file_data: List of dictionaries with file information from RAG,
                     each containing 'file' and 'content' keys
            
        Returns:
            Formatted string with file descriptions in Markdown format
        """
        if not file_data:
            self.logger.warning("No file data provided for README generation")
            return "No detailed file descriptions available."
            
        file_descriptions_parts = []
        
        for file_info in file_data:
            filepath = file_info.get('file', '')
            content = file_info.get('content', '')
            
            if not filepath or not content:
                self.logger.warning(f"Incomplete file information: {file_info}")
                continue
                
            # Extract basename for cleaner representation
            doc_name = os.path.basename(filepath)
            
            try:
                # Generate description for this file
                description = self.generator.generate_file_description(content, doc_name)
                file_descriptions_parts.append(f"- `{doc_name}`: {description}")
            except Exception as e:
                self.logger.error(f"Error generating description for {doc_name}: {e}")
                file_descriptions_parts.append(f"- `{doc_name}`: No description available (error during generation)")
            
        # Join all file descriptions
        return "\n".join(file_descriptions_parts) if file_descriptions_parts else \
               "No detailed file descriptions available."
    
    def generate_readme(self, 
                       project_info: Dict[str, Any], 
                       file_data: List[Dict[str, str]], 
                       repo_path: str,
                       skip_dirs: List[str]) -> Union[str, None]:
        """
        Generate README content based on project information and file data.
        
        Args:
            project_info: Dictionary containing project information
            file_data: List of dictionaries with file information from RAG
            repo_path: Path to the repository
            skip_dirs: Directories to skip when generating file tree
            
        Returns:
            Generated README content as a string or None if generation fails
        """
        try:
            project_name = project_info.get('name', os.path.basename(repo_path))
            
            # Generate file structure tree
            file_structure_md = get_file_tree(
                repo_path, 
                skip_dirs=skip_dirs, 
                file_ext_filter=project_info.get('file_ext', '.py'), 
                max_depth=6
            )
            
            # Process file descriptions from RAG results
            file_descriptions = self.process_file_descriptions(file_data)
            
            # Generate the README content
            self.logger.info(f"Generating README for {project_name}")
            readme_content = self.generator.generate_readme(
                project_name=project_name,
                file_structure=file_structure_md,
                key_elements_summary="",  # We're not using parsed data for simplicity
                file_descriptions=file_descriptions
            )
            
            if not readme_content:
                self.logger.error("README generation failed - empty content returned")
                return None
                
            return readme_content
            
        except Exception as e:
            self.logger.exception(f"Error generating README: {e}")
            return None
    
    def save_readme(self, content: Optional[str], output_path: str) -> bool:
        """
        Save README content to a file.
        
        Args:
            content: README content or None if generation failed
            output_path: Path where to save the README
            
        Returns:
            True if saving was successful, False otherwise
        """
        if not content:
            self.logger.error("Cannot save README: content is None")
            return False
            
        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"README saved to {output_path}")
            return True
        except IOError as e:
            self.logger.error(f"Error writing README to {output_path}: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"Unexpected error saving README: {e}")
            return False
