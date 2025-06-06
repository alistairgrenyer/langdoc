# embedding.py
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter # Or CharacterTextSplitter, PythonCodeTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS # Or Chroma
from langchain.docstore.document import Document
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found. Please set it in your .env file or environment variables.")

class CodeEmbedder:
    FAISS_INDEX_DIR = ".langdoc_index" # Default directory to save/load FAISS index
    FAISS_INDEX_NAME = "faiss_index"    # Default name for the FAISS index files

    def __init__(self, model_name="text-embedding-ada-002", chunk_size=1000, chunk_overlap=100):
        self.embeddings_model = OpenAIEmbeddings(model=model_name, openai_api_key=OPENAI_API_KEY)
        # Consider Langchain's PythonCodeTextSplitter for more intelligent chunking of code
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            # separators=["\n\n", "\n", " ", "", "\nclass ", "\ndef "] # Customize as needed
        )
        self.vector_store = None

    def create_documents_from_parsed_data(self, parsed_files: List[Dict[str, Any]]) -> List[Document]:
        """Creates LangChain Document objects from parsed file data."""
        documents = []
        for parsed_file in parsed_files:
            if "error" in parsed_file:
                continue
            
            file_path = parsed_file['file_path']
            
            # Option 1: Embed whole file content
            # documents.append(Document(page_content=parsed_file['content'], metadata={"source": file_path, "type": "file"}))

            # Option 2: Embed definitions (functions/classes) as separate documents
            for definition in parsed_file.get('definitions', []):
                code_content = definition.get('code', '')
                if not code_content.strip(): # Skip empty code blocks
                    continue
                
                metadata = {
                    "source": file_path,
                    "type": definition['type'],
                    "name": definition['name'],
                    "lineno": definition['lineno'],
                    "end_lineno": definition['end_lineno']
                }
                # Create a LangChain document. Content could be just the code, or code + docstring.
                # For RAG, it's often better to have more context.
                doc_content = f"File: {file_path}\nType: {definition['type']}\nName: {definition['name']}\n\nCode:\n{code_content}"
                if definition.get('docstring'):
                    doc_content += f"\n\nDocstring:\n{definition['docstring']}"
                
                documents.append(Document(page_content=doc_content, metadata=metadata))
        return documents

    def build_vector_store(self, documents: List[Document]):
        """Builds or updates the FAISS vector store with the given documents."""
        if not documents:
            print("No documents to build vector store.")
            return
        
        # Split documents if they are too large for the embedding model context window
        # This might not be necessary if documents are already granular (e.g., one per function)
        split_docs = self.text_splitter.split_documents(documents)
        
        if not OPENAI_API_KEY:
            print("Cannot build vector store: OPENAI_API_KEY is not set.")
            self.vector_store = None # Ensure it's None if we can't build
            return

        try:
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(split_docs, self.embeddings_model)
            else:
                # FAISS typically rebuilds or adds. For in-memory, adding might be fine.
                # For persistent stores, check their specific add_documents methods.
                self.vector_store.add_documents(split_docs)
            print(f"Vector store built/updated with {len(split_docs)} chunks.")
        except Exception as e:
            print(f"Error building FAISS vector store: {e}")
            self.vector_store = None # Ensure it's None on error

    def save_vector_store(self, path: str = FAISS_INDEX_DIR, index_name: str = FAISS_INDEX_NAME) -> bool:
        """Saves the FAISS vector store to disk."""
        if self.vector_store is None:
            print("No vector store to save.")
            return False
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            self.vector_store.save_local(folder_path=path, index_name=index_name)
            print(f"Vector store saved to {os.path.join(path, index_name)}")
            return True
        except Exception as e:
            print(f"Error saving FAISS vector store: {e}")
            return False

    def load_vector_store(self, path: str = FAISS_INDEX_DIR, index_name: str = FAISS_INDEX_NAME) -> bool:
        """Loads the FAISS vector store from disk."""
        index_path = os.path.join(path, index_name + ".faiss") # FAISS saves as .faiss and .pkl
        if not os.path.exists(index_path):
            print(f"No FAISS index found at {index_path}. Please run the 'parse' command first.")
            return False
        if not OPENAI_API_KEY:
            print("Cannot load vector store: OPENAI_API_KEY is not set for embeddings.")
            return False
        try:
            self.vector_store = FAISS.load_local(
                folder_path=path, 
                embeddings=self.embeddings_model, 
                index_name=index_name,
                allow_dangerous_deserialization=True # Required by LangChain for FAISS
            )
            print(f"Vector store loaded from {os.path.join(path, index_name)}")
            return True
        except Exception as e:
            print(f"Error loading FAISS vector store: {e}")
            self.vector_store = None
            return False

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Performs similarity search on the vector store."""
        if self.vector_store is None:
            print("Vector store not initialized. Please parse and build first.")
            return []
        if not OPENAI_API_KEY:
            print("Cannot perform search: OPENAI_API_KEY is not set.")
            return []
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []

# Example usage (for testing this module independently)
if __name__ == '__main__':
    from parser import get_file_paths, parse_python_file
    import shutil # For cleanup

    if not OPENAI_API_KEY:
        print("Skipping embedding.py example: OPENAI_API_KEY not set.")
    else:
        print("Running embedding.py example...")
        sample_repo_path = '.' # Current directory
        py_files = get_file_paths(sample_repo_path, skip_dirs=['.git', 'venv', '__pycache__', 'docs', 'tests', '.langdoc_index'])
        
        parsed_files_data = []
        for py_file in py_files:
            if os.path.basename(py_file) not in [os.path.basename(__file__), 'cli.py', 'docgen.py', 'utils.py']:
                parsed_data = parse_python_file(py_file)
                if "error" not in parsed_data and parsed_data.get('definitions'):
                    parsed_files_data.append(parsed_data)
        
        if not parsed_files_data:
            print("No parsable Python files with definitions found for the example.")
        else:
            print(f"Found {len(parsed_files_data)} files with definitions for embedding example.")
            embedder = CodeEmbedder()
            documents_to_embed = embedder.create_documents_from_parsed_data(parsed_files_data)
            
            if documents_to_embed:
                print(f"Created {len(documents_to_embed)} LangChain documents for embedding.")
                embedder.build_vector_store(documents_to_embed)
                
                if embedder.vector_store:
                    print("Initial vector store built.")
                    saved_successfully = embedder.save_vector_store()

                    if saved_successfully:
                        print("Attempting to load vector store...")
                        embedder_loaded = CodeEmbedder()
                        loaded_successfully = embedder_loaded.load_vector_store()

                        if loaded_successfully and embedder_loaded.vector_store:
                            query = "How is data parsed?"
                            print(f"\nPerforming similarity search for: '{query}'")
                            search_results = embedder_loaded.similarity_search(query)
                            if search_results:
                                for i, doc_result in enumerate(search_results):
                                    print(f"\nResult {i+1}:")
                                    print(f"  Source: {doc_result.metadata.get('source')}, Name: {doc_result.metadata.get('name')}")
                                    # print(f"  Content snippet: {doc_result.page_content[:200]}...")
                            else:
                                print("No search results found.")
                        else:
                            print("Failed to load vector store or loaded store is invalid.")
                    else:
                        print("Failed to save vector store, skipping load test.")
                else:
                    print("Initial vector store build failed.")

                # Clean up dummy index directory if it was created
                if os.path.exists(CodeEmbedder.FAISS_INDEX_DIR):
                    print(f"Cleaning up {CodeEmbedder.FAISS_INDEX_DIR}...")
                    shutil.rmtree(CodeEmbedder.FAISS_INDEX_DIR)
            else:
                print("No documents were created for embedding.")

