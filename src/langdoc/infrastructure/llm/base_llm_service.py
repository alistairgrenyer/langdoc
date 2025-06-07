"""Base LLM service implementation."""

import os
from typing import Dict, List, Optional

import rich.console
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI

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
            verbose=True,
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
                HumanMessagePromptTemplate.from_template("{prompt}"),
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
            f"Below is context information from the codebase to help you "
            f"generate accurate documentation:\n"
            f"{context_text}\n\n"
            f"Generate documentation that is clear, concise, and follows best practices. "
            f"The documentation should feel like it was written by a human - conversational "
            f"yet professional - and accurately reflect the codebase structure and functionality."
        )
        
        return system_prompt
