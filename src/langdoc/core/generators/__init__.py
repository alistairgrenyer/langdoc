"""
Base generator classes for various LLM-powered documentation tasks.
"""
import os
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

class Generator:
    """Base class for all LLM-powered generators."""
    
    def __init__(self, model_name="gpt-3.5-turbo", openai_api_key=None):
        """Initialize the Generator with specified LLM model.
        
        Args:
            model_name: Name of the LLM model to use, defaults to 'gpt-3.5-turbo'
            openai_api_key: API key for OpenAI, if None uses environment variable
        """
        self.model_name = model_name
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            self.llm = None
            print(f"Warning: No OpenAI API key found for {self.__class__.__name__}. LLM features disabled.")
            return
            
        self.llm = ChatOpenAI(model=model_name, openai_api_key=self.api_key, temperature=0.2)
        self.output_parser = StrOutputParser()
    
    def _create_chain(self, prompt_template):
        """Create a LangChain chain with the specified prompt template.
        
        Args:
            prompt_template: ChatPromptTemplate to use in the chain
            
        Returns:
            A callable chain that accepts prompt variables and returns generated text
        """
        if not self.llm:
            return None
        return prompt_template | self.llm | self.output_parser
