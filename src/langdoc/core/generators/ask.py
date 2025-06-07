"""
Specialized generator for answering questions about the codebase.
"""
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from . import Generator


class AskGenerator(Generator):
    """Specialized generator for answering questions about the codebase."""
    
    def __init__(self, model_name="gpt-3.5-turbo", openai_api_key=None):
        """Initialize the AskGenerator.
        
        Args:
            model_name: Name of the LLM model to use, defaults to 'gpt-3.5-turbo'
            openai_api_key: API key for OpenAI, if None uses environment variable
        """
        super().__init__(model_name, openai_api_key)
        
        # Initialize the RAG prompt template
        self.rag_prompt = ChatPromptTemplate.from_template("""
        You are an AI assistant helping to answer questions about a codebase.
        Use the following retrieved code context to answer the question.
        If you don't know the answer from the context, say that you don't know.
        Be concise and focus on the information present in the provided context.

        Context:
        {context}

        Question: {input}

        Answer:
        """)

    def generate_answer(self, question: str, retriever) -> Dict[str, Any]:
        """Generate an answer to the given question using the RAG approach.
        
        Args:
            question: The question to answer
            retriever: The retriever to use for finding relevant documents
            
        Returns:
            A dictionary containing the answer and retrieved context
        """
        if not self.llm:
            return {
                "answer": "Unable to generate answer: LLM not initialized. Please check your OpenAI API key.",
                "context": []
            }
        
        try:
            # Create the document chain for combining documents into context
            document_chain = create_stuff_documents_chain(self.llm, self.rag_prompt)
            
            # Create the retrieval chain with the provided retriever
            retrieval_chain = create_retrieval_chain(retriever, document_chain)
            
            # Execute the chain
            response = retrieval_chain.invoke({"input": question})
            
            # Return response with proper fallback
            return {
                "answer": response.get('answer', 
                                     "Sorry, I couldn't formulate an answer based on the retrieved context."),
                "context": response.get('context', [])
            }
        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "context": []
            }
            
    def generate_direct_answer(self, question: str, documents: List[Document]) -> str:
        """Generate an answer to the given question using provided documents directly.
        
        Args:
            question: The question to answer
            documents: The list of documents to use as context
            
        Returns:
            The generated answer as a string
        """
        if not self.llm:
            return "Unable to generate answer: LLM not initialized. Please check your OpenAI API key."
        
        try:
            # Create the document chain for combining documents into context
            document_chain = create_stuff_documents_chain(self.llm, self.rag_prompt)
            
            # Execute the chain directly with documents
            response = document_chain.invoke({
                "input": question,
                "context": documents
            })
            
            # Return answer with proper fallback
            return response.get('answer', 
                              "Sorry, I couldn't formulate an answer based on the provided context.")
        except Exception as e:
            return f"Error generating answer: {str(e)}"
