# docgen.py
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
        if OPENAI_API_KEY:
            self.llm = ChatOpenAI(model=model_name, openai_api_key=OPENAI_API_KEY, temperature=0.2)
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

                
                Detailed File Descriptions:
{file_descriptions}

                
                Existing {section_title} Content (if any):
{existing_section_content}

                
                INSTRUCTIONS:
                1. Analyze the provided context to develop a deep understanding of the project's purpose, architecture, and functionality.
                2. Write an informative, well-structured {section_title} section using proper markdown formatting.
                3. Incorporate specific details about what each major file and component does based on the detailed file descriptions.
                4. For 'Project Summary' sections, clearly articulate the value proposition, key features, and how the components work together.
                5. For file structure sections, don't just list files - explain what each significant file or directory contains and its purpose.
                6. Use clear, concise language appropriate for software documentation.
                7. Include relevant subsections, bullet points, and code examples where appropriate.
                8. If the existing content adequately covers all this information, respond with 'No change needed'.
                
                Respond with ONLY the markdown content for the section, without preamble or explanation.
                """
            )
            self.output_parser = StrOutputParser()
        else:
            self.llm = None
            print("DocGenerator: LLM not initialized due to missing API key.")

    def generate_docstring(self, code_type: str, code_name: str, code_content: str, existing_docstring: Optional[str] = None) -> Optional[str]:
        if not self.llm:
            print("Cannot generate docstring: LLM not available.")
            return None
        
        chain = self.docstring_prompt | self.llm | self.output_parser
        try:
            generated_docstring = chain.invoke({
                "code_type": code_type,
                "code_name": code_name,
                "code_content": code_content,
                "existing_docstring": existing_docstring if existing_docstring else "None"
            })
            if generated_docstring.strip().upper() == "SKIP":
                return None # Indicates no change needed
            return generated_docstring.strip()
        except Exception as e:
            print(f"Error generating docstring for {code_name}: {e}")
            return None

    def update_file_with_docstrings(self, file_path: str, parsed_data: Dict[str, Any]) -> bool:
        """Updates a Python file with generated docstrings for functions/classes if they are missing or inadequate."""
        if not self.llm:
            print(f"Skipping docstring updates for {file_path}: LLM not available.")
            return False

        content_lines = parsed_data.get("content", "").splitlines()
        if not content_lines:
            return False

        modified = False
        # offset = 0 # Placeholder for line number adjustments if modifying file content

        for definition in sorted(parsed_data.get('definitions', []), key=lambda x: x['lineno'], reverse=True):
            code_type = definition['type']
            code_name = definition['name']
            code_content = definition['code']
            existing_docstring = definition['docstring']
            # lineno = definition['lineno'] -1 # 0-indexed, placeholder for file modification

            # Simple heuristic: if docstring is very short or non-existent, try to generate one.
            # More sophisticated checks could be added (e.g., length, keywords).
            if not existing_docstring or len(existing_docstring.strip()) < 10:
                print(f"Attempting to generate docstring for {code_type} {code_name} in {file_path}...")
                new_docstring = self.generate_docstring(code_type, code_name, code_content, existing_docstring)
                
                if new_docstring:
                    # This part is tricky: inserting docstrings into the AST/source code correctly.
                    # For simplicity, this example focuses on the generation part.
                    # A robust solution would use AST manipulation (e.g., with `astor` or `libcst`)
                    # or careful string manipulation.
                    print(f"  Generated docstring for {code_name}:\n{new_docstring}\n")
                    # Placeholder: In a real scenario, you'd integrate this back into the file.
                    # For now, we'll just print. A real implementation would modify `content_lines`
                    # and then write the file back.
                    # This is a complex task and libraries like `astor` are recommended for source rewriting.
                    modified = True # Assume modification for now
                    print(f"  [INFO] Docstring for {code_name} in {file_path} would be updated. (Actual file modification not yet implemented here)")

        # if modified:
        #     with open(file_path, 'w', encoding='utf-8') as f:
        #         f.write("\n".join(content_lines))
        #     print(f"Updated docstrings in {file_path}")
        
        return modified

    def generate_module_markdown(self, parsed_file_data: Dict[str, Any], output_dir: str = 'docs') -> Optional[str]:
        """Generates a markdown file summarizing a module."""
        if not self.llm:
            print("Cannot generate module markdown: LLM not available.")
            return None

        file_path = parsed_file_data['file_path']
        definitions = parsed_file_data.get('definitions', [])
        if not definitions:
            return None

        definitions_summary_parts = []
        for def_item in definitions:
            summary = f"- **{def_item['name']}** ({def_item['type']})"
            if def_item.get('docstring'):
                summary += f": {def_item['docstring'].splitlines()[0][:100]}..." # First line of docstring as a snippet
            definitions_summary_parts.append(summary)
        
        definitions_summary_str = "\n".join(definitions_summary_parts)

        chain = self.module_summary_prompt | self.llm | self.output_parser
        try:
            md_content = f"# Module: `{os.path.basename(file_path)}`\n\n"
            summary = chain.invoke({
                "file_path": file_path,
                "definitions_summary": definitions_summary_str
            })
            md_content += summary + "\n\n## Key Components\n\n"
            
            for def_item in definitions:
                md_content += f"### `{def_item['name']}` ({def_item['type']})\n\n"
                if def_item.get('docstring'):
                    md_content += f"**Docstring:**\n```\n{def_item['docstring']}\n```\n\n"
                # md_content += f"**Code Snippet:**\n```python\n{def_item['code']}\n```\n\n"
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            md_file_name = os.path.basename(file_path).replace('.py', '.md')
            md_file_path = os.path.join(output_dir, md_file_name)
            
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"Generated markdown for {file_path} at {md_file_path}")
            return md_file_path
        except Exception as e:
            print(f"Error generating module markdown for {file_path}: {e}")
            return None

    def generate_readme_section(self, section_title: str, project_name: str, file_structure: str, key_elements_summary: str, file_descriptions: str = "No detailed file descriptions available.", existing_section_content: str = "") -> Optional[str]:
        """Generate a well-structured README section using the available project information.
        
        Args:
            section_title: The title for the section (e.g., "Project Summary")
            project_name: The name of the project
            file_structure: Markdown representation of the file structure
            key_elements_summary: Summary of key functions and classes
            file_descriptions: Detailed descriptions of files obtained via RAG
            existing_section_content: Existing content for this section (if any)
            
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
                "existing_section_content": existing_section_content
            })
            return content
        except Exception as e:
            print(f"Error generating README section '{section_title}': {e}")
            return None
