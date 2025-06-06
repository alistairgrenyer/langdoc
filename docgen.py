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
                "Generate a concise and informative docstring for the following {code_type} named '{code_name}'. "
                "The code is:\n\n```python\n{code_content}```\n\nConsider its purpose, arguments (if any), and what it returns (if applicable). "
                "The existing docstring is: '{existing_docstring}'. "
                "If the existing docstring is adequate, respond with 'SKIP'. Otherwise, provide the new docstring only, without any preamble."
            )
            self.module_summary_prompt = ChatPromptTemplate.from_template(
                "Provide a brief summary for a Python module located at '{file_path}'. "
                "The module contains the following functions and classes: {definitions_summary}. "
                "Focus on the overall purpose and key functionalities of the module. "
                "Respond with the markdown summary only."
            )
            self.readme_section_prompt = ChatPromptTemplate.from_template(
                "Given the following information about a project, generate the '{section_title}' section for a README.md file.\n\n"
                "Project Name: {project_name}\n"
                "File Structure Overview:\n{file_structure}\n\n"
                "Key Functions/Classes Summary:\n{key_elements_summary}\n\n"
                "Existing {section_title} Content (if any):\n{existing_section_content}\n\n"
                "Generate a concise and informative {section_title} section. If the existing content is good, you can suggest minor improvements or state 'No change needed'."
                "Respond with the markdown for the section only."
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

    def generate_readme_section(self, section_title: str, project_name: str, file_structure: str, key_elements_summary: str, existing_section_content: str = "") -> Optional[str]:
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
                "existing_section_content": existing_section_content
            })
            return content
        except Exception as e:
            print(f"Error generating README section '{section_title}': {e}")
            return None

# Example Usage (for testing this module independently)
if __name__ == '__main__':
    from parser import parse_python_file # Assuming parser.py is in the same directory

    if not OPENAI_API_KEY:
        print("Skipping docgen.py example: OPENAI_API_KEY not set.")
    else:
        print("Running docgen.py example...")
        # Create a dummy Python file for testing
        dummy_file_content = """
def greet(name):
    # No docstring here
    return f"Hello, {name}"

class Calculator:
    \"\"\"A simple calculator class.\"\"\"
    def add(self, a, b):
        # Missing docstring for method
        return a + b
"""
        dummy_file_path = "_temp_dummy_module.py"
        with open(dummy_file_path, "w") as f:
            f.write(dummy_file_content)

        parsed_info = parse_python_file(dummy_file_path)
        doc_gen = DocGenerator()

        if parsed_info and "error" not in parsed_info:
            # Test docstring generation (will print, not modify file in this example)
            print("\n--- Testing Docstring Generation ---")
            doc_gen.update_file_with_docstrings(dummy_file_path, parsed_info)

            # Test module markdown generation
            print("\n--- Testing Module Markdown Generation ---")
            md_path = doc_gen.generate_module_markdown(parsed_info, output_dir='temp_docs')
            if md_path and os.path.exists(md_path):
                print(f"Module markdown generated at: {md_path}")
                # Clean up dummy markdown dir
                # os.remove(md_path)
                # os.rmdir('temp_docs')
            else:
                print("Failed to generate module markdown or file not found.")
            
            # Test README section generation
            print("\n--- Testing README Section Generation ---")
            project_fs = "- cli.py\n- parser.py\n- embedding.py\n- docgen.py"
            key_elements = "- `parse()` in cli.py: Parses the repo.\n- `CodeEmbedder` in embedding.py: Handles embeddings."
            summary_section = doc_gen.generate_readme_section(
                section_title="Project Summary",
                project_name="LangDoc Test",
                file_structure=project_fs,
                key_elements_summary=key_elements,
                existing_section_content="This is an old summary."
            )
            if summary_section:
                print(f"Generated 'Project Summary' section:\n{summary_section}")

        # Clean up dummy file
        if os.path.exists(dummy_file_path):
            os.remove(dummy_file_path)
        if os.path.exists('temp_docs'):
            if md_path and os.path.exists(md_path):
                os.remove(md_path)
            os.rmdir('temp_docs')

