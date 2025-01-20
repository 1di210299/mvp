import os
import configparser
import tiktoken
from queue import Queue
from langchain.schema import Document
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain.chains import ConversationalRetrievalChain

from dotenv import load_dotenv
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
confluence_api_key = os.getenv("CONFLUENCE_API_KEY")

class Embedder:
    def __init__(self, st) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(".streamlit/defaults.toml")
        self.default_folder_path = self.config["DEFAULT"].get("folder_path") or os.getcwd()
        self.st = st  # Save reference to st
        
        self.model = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=2000,
            model_kwargs={
                "presence_penalty": 0.6,
                "frequency_penalty": 0.6
            }
        )

        self.hf = OpenAIEmbeddings()
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.MyQueue = Queue(maxsize=2)
        self.docs = []
        self.db = None
        self.retriever = None

    def add_document(self, document):
        """Add a document to the document list."""
        try:
            self.docs.append(document)
            print(f"Document added. Total documents: {len(self.docs)}")
            
            # Recreate database if necessary
            if len(self.docs) > 0 and self.hf is not None:
                self.db = DocArrayInMemorySearch.from_documents(self.docs, self.hf)
                self.retriever = self.db.as_retriever(
                    search_type="mmr",
                    search_kwargs={
                        "k": 5,
                        "fetch_k": 20,
                        "lambda_mult": 0.7,
                    }
                )
                print("Vector store updated")
        except Exception as e:
            print(f"Error adding document: {str(e)}")

    def retrieve_results(self, query):
        try:
            print("\n=== Debug Information ===")
            print(f"Total documents loaded in Embedder: {len(self.docs)}")
            
            if not self.docs:
                return "There are no documents uploaded to analyze. Please upload some documents first."

            self.db = DocArrayInMemorySearch.from_documents(self.docs, self.hf)
            self.retriever = self.db.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 5,
                    "fetch_k": 20,
                    "lambda_mult": 0.7,
                }
            )

            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.model,
                retriever=self.retriever,
                return_source_documents=True,
            )

            chat_history = list(self.MyQueue.queue)
            result = qa_chain({"question": query, "chat_history": chat_history})
            
            # Add to chat history
            self.add_to_queue((query, result['answer']))
            
            return result['answer']

        except Exception as e:
            print(f"Error in retrieve_results: {str(e)}")
            return f"Error al procesar la consulta: {str(e)}"

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text using the configured encoding"""
        return len(self.encoding.encode(text))

    def count_total_tokens(self, prompt: str) -> int:
        self.prompt_total_tokens = len(self.encoding.encode(prompt))
        return self.prompt_total_tokens

    def send_request(self):
        try:
            query = self.st.session_state.prompt
            return self.retrieve_results(query)
        except Exception as e:
            return f"Error: {str(e)}"

    def add_to_queue(self, value):
        if self.MyQueue.full():
            self.MyQueue.get()
        self.MyQueue.put(value)

    def set_default_folder_path(self, folder_path: str):
        """Set a new default directory and update the configuration."""

        self.config["DEFAULT"]["FOLDER_PATH"] = folder_path
        with open(".streamlit/defaults.toml", "w") as configfile:
            self.config.write(configfile)

    def get_default_folder_path(self) -> str:

        """Gets the configured default directory."""
        return self.config["DEFAULT"]["FOLDER_PATH"]

    def count_tokens_from_url(self, url, content_type=''):
        """Count content tokens based on URL (Jira or Confluence)"""
        try:
            if not url:
                return 0
                
            # Get content by type
            content = ""
            if content_type == 'jira':
                for doc in self.st.session_state.jira_docs:
                    if doc.metadata.get('url') == url:
                        content = doc.page_content
                        break
            elif content_type == 'confluence':
                for doc in self.st.session_state.confluence_docs:
                    if doc.metadata.get('url') == url:
                        content = doc.page_content
                        break
                        
            return self.count_tokens(content)
            
        except Exception as e:
            print(f"Error counting tokens from URL: {str(e)}")
            return 0

    def count_tokens_from_file(self, file_path):
        """Count local file tokens"""
        try:
            if not file_path or not os.path.exists(file_path):
                return 0
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return self.count_tokens(content)
                
        except Exception as e:
            print(f"Error counting tokens from file: {str(e)}")
            return 0

    def get_total_tokens(self):
        """Calculate the total tokens of all selected resources"""
        total = 0
        
        try:
            # Count tokens from current prompt
            if hasattr(self.st.session_state, 'prompt'):
                total += self.count_tokens(self.st.session_state.prompt or "")

            # Counting Jira Tokens
            if hasattr(self.st.session_state, 'selected_resources'):
                for url, info in self.st.session_state.selected_resources['jira'].items():
                    if info['selected']:
                        total += self.count_tokens_from_url(url, 'jira')

                # Counting Confluence Tokens
                for url, info in self.st.session_state.selected_resources['confluence'].items():
                    if info['selected']:
                        total += self.count_tokens_from_url(url, 'confluence')

                # Count local file tokens
                for path, info in self.st.session_state.selected_resources['files'].items():
                    if info['selected']:
                        total += self.count_tokens_from_file(path)

            # Add GitHub doc tokens if they exist
            if hasattr(self.st.session_state, 'utils_docs'):
                for doc in self.st.session_state.utils_docs:
                    if doc.metadata.get('type') == 'github':
                        repo_url = doc.metadata.get('repository_url')
                        if repo_url in self.st.session_state.selected_resources['github'] and \
                        self.st.session_state.selected_resources['github'][repo_url]['selected']:
                            total += self.count_tokens(doc.page_content)

            return total
            
        except Exception as e:
            print(f"Error calculating total tokens: {str(e)}")
            return 0

    def get_token_breakdown(self):
        """Obtiene un desglose detallado del uso de tokens"""
        breakdown = {
            'prompt': 0,
            'jira': 0,
            'confluence': 0,
            'files': 0,
            'github': 0
        }
        
        try:
            # Prompt Tokens
            if hasattr(self.st.session_state, 'prompt'):
                breakdown['prompt'] = self.count_tokens(self.st.session_state.prompt or "")

            # Tokens of each resource type
            if hasattr(self.st.session_state, 'selected_resources'):
                for url, info in self.st.session_state.selected_resources['jira'].items():
                    if info['selected']:
                        breakdown['jira'] += self.count_tokens_from_url(url, 'jira')

                for url, info in self.st.session_state.selected_resources['confluence'].items():
                    if info['selected']:
                        breakdown['confluence'] += self.count_tokens_from_url(url, 'confluence')

                for path, info in self.st.session_state.selected_resources['files'].items():
                    if info['selected']:
                        breakdown['files'] += self.count_tokens_from_file(path)

                # GitHub repos
                if hasattr(self.st.session_state, 'utils_docs'):
                    for doc in self.st.session_state.utils_docs:
                        if doc.metadata.get('type') == 'github':
                            repo_url = doc.metadata.get('repository_url')
                            if repo_url in self.st.session_state.selected_resources['github'] and \
                            self.st.session_state.selected_resources['github'][repo_url]['selected']:
                                breakdown['github'] += self.count_tokens(doc.page_content)

            return breakdown
            
        except Exception as e:
            print(f"Error getting token breakdown: {str(e)}")
            return breakdown