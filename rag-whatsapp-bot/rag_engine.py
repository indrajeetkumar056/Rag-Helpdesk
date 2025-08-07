import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# LangChain imports
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_ollama import OllamaLLM

# Load environment variables
load_dotenv()

class RAGEngine:
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.llm = None
        self.retrieval_chain = None
        self.text_splitter = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize LangChain components"""
        try:
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            
            # Initialize LLM (using Ollama)
            self.llm = OllamaLLM(model="phi4-mini:latest")
            
            # Create prompt template specifically for NSE agent responses
            prompt = ChatPromptTemplate.from_template("""
            You are an NSE (National Stock Exchange) helpdesk assistant. Use the following historical Q&A examples from NSE agents to answer the client's question.
            
            If different answers exist in different scenarios (e.g., activation vs reactivation), explain the difference clearly.
            
            Context (Historical NSE Agent Responses):
            {context}
            
            Client Question: {input}
            
            Based on the NSE agent responses above, provide a clear and helpful answer. Be confident and professional like an NSE agent would be.
            IMPORTANT: Summarize multiple solutions into a single, clear response under 1600 characters.
            """)
            
            # Create document chain
            document_chain = create_stuff_documents_chain(self.llm, prompt)
            
            # Initialize vector store if it exists
            if os.path.exists("vector_store"):
                self.vector_store = FAISS.load_local("vector_store", self.embeddings,allow_dangerous_deserialization=True)
                retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                self.retrieval_chain = create_retrieval_chain(retriever, document_chain)
                self.logger.info("Vector store loaded successfully")
            else:
                self.logger.info("No existing vector store found. Will be created when documents are added.")
                
        except Exception as e:
            self.logger.error(f"Error initializing RAG components: {str(e)}")
            raise
    
    def initialize(self):
        """Public method to initialize the RAG engine"""
        try:
            # Load CSV data first
            self._load_csv_data()
            # Then load existing documents from database
            self._load_documents_from_db()
            self.logger.info("RAG engine initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing RAG engine: {str(e)}")
    
    def _load_csv_data(self):
        """Load data from call.csv and create vector store"""
        try:
            csv_path = "call.csv"
            if not os.path.exists(csv_path):
                self.logger.warning(f"CSV file {csv_path} not found. Skipping CSV data loading.")
                return
            
            # Load CSV data
            df = pd.read_csv(csv_path)
            self.logger.info(f"Loaded CSV with {len(df)} rows")
            
            # Check required columns
            required_columns = ['Query', 'Response']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns in CSV: {missing_columns}")
                return
            
            # Create documents from CSV data
            docs = []
            for index, row in df.iterrows():
                # Create a document with both query and response for better context
                content = f"Client Question: {row['Query']}\nNSE Agent Response: {row['Response']}"
                
                # Add Sr no. as metadata if available
                metadata = {"source": "call.csv", "row_id": index}
                if 'Sr no.' in df.columns:
                    metadata["sr_no"] = row['Sr no.']
                
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                docs.append(doc)
            
            if docs:
                # Split documents
                split_docs = self.text_splitter.split_documents(docs)
                
                # Create vector store
                self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
                
                # Save vector store locally
                self.vector_store.save_local("vector_store")
                
                # Create retrieval chain
                retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                self.retrieval_chain = create_retrieval_chain(retriever, self._create_document_chain())
                
                self.logger.info(f"Loaded {len(docs)} Q&A pairs from CSV into vector store")
                
                # Save to database for persistence
                self._save_csv_to_database(df)
            else:
                self.logger.warning("No valid documents found in CSV")
                
        except Exception as e:
            self.logger.error(f"Error loading CSV data: {str(e)}")
    
    def _save_csv_to_database(self, df):
        """Save CSV data to SQLite database for persistence"""
        try:
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            
            # Create table for CSV data if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS csv_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sr_no TEXT,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    source TEXT DEFAULT 'call.csv',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Clear existing CSV data
            cursor.execute('DELETE FROM csv_data WHERE source = "call.csv"')
            
            # Insert new data
            for index, row in df.iterrows():
                sr_no = row.get('Sr no.', '') if 'Sr no.' in df.columns else ''
                cursor.execute('''
                    INSERT INTO csv_data (sr_no, query, response, source)
                    VALUES (?, ?, ?, ?)
                ''', (str(sr_no), row['Query'], row['Response'], 'call.csv'))
            
            conn.commit()
            conn.close()
            self.logger.info("CSV data saved to database")
            
        except Exception as e:
            self.logger.error(f"Error saving CSV to database: {str(e)}")
    
    def _load_documents_from_db(self):
        """Load documents from SQLite database and create vector store"""
        try:
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            
            # Load both CSV data and additional documents
            cursor.execute('''
                SELECT sr_no, query, response, source FROM csv_data 
                UNION ALL
                SELECT NULL, title, content, 'manual' FROM documents
            ''')
            documents = cursor.fetchall()
            conn.close()
            
            if documents and not self.vector_store:
                # Create documents for LangChain
                docs = []
                for sr_no, query, response, source in documents:
                    if source == 'call.csv':
                        content = f"Client Question: {query}\nNSE Agent Response: {response}"
                        metadata = {"source": source, "sr_no": sr_no}
                    else:
                        content = response  # For manual documents, response is the content
                        metadata = {"source": source, "title": query}
                    
                    doc = Document(
                        page_content=content,
                        metadata=metadata
                    )
                    docs.append(doc)
                
                # Split documents
                split_docs = self.text_splitter.split_documents(docs)
                
                # Create vector store
                self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
                
                # Save vector store locally
                self.vector_store.save_local("vector_store")
                
                # Create retrieval chain
                retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                self.retrieval_chain = create_retrieval_chain(retriever, self._create_document_chain())
                
                self.logger.info(f"Loaded {len(documents)} documents into vector store")
            elif not documents:
                self.logger.info("No documents found in database")
                
        except Exception as e:
            self.logger.error(f"Error loading documents from database: {str(e)}")
    
    def _create_document_chain(self):
        """Create document chain with prompt template for NSE responses"""
        prompt = ChatPromptTemplate.from_template("""
        You are an NSE (National Stock Exchange) helpdesk assistant. Use the following historical Q&A examples from NSE agents to answer the client's question.
        
        If different answers exist in different scenarios (e.g., activation vs reactivation), explain the difference clearly.
        
        Context (Historical NSE Agent Responses):
        {context}
        
        Client Question: {input}
        
        Based on the NSE agent responses above, provide a clear and helpful answer. Be confident and professional like an NSE agent would be.
        """)
        
        return create_stuff_documents_chain(self.llm, prompt)
    
    def add_document(self, title: str, content: str):
        """Add a new document to the knowledge base"""
        try:
            # Create document
            doc = Document(
                page_content=content,
                metadata={"title": title, "source": "manual"}
            )
            
            # Split document
            split_docs = self.text_splitter.split_documents([doc])
            
            if self.vector_store is None:
                # Create new vector store
                self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
            else:
                # Add to existing vector store
                self.vector_store.add_documents(split_docs)
            
            # Save vector store
            self.vector_store.save_local("vector_store")
            
            # Recreate retrieval chain
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            self.retrieval_chain = create_retrieval_chain(retriever, self._create_document_chain())
            
            self.logger.info(f"Document '{title}' added successfully")
            
        except Exception as e:
            self.logger.error(f"Error adding document: {str(e)}")
            raise
    
    def get_response(self, query: str) -> str:
        """Get response for a user query based on NSE agent responses"""
        try:
            if self.retrieval_chain is None:
                return "I'm sorry, but I don't have any NSE knowledge base loaded yet. Please ensure the call.csv file is present."
            
            # Get response from RAG chain
            response = self.retrieval_chain.invoke({"input": query})
            
            return response.get("answer", "I'm sorry, I couldn't generate a response based on the available NSE agent data.")
            
        except Exception as e:
            self.logger.error(f"Error getting response: {str(e)}")
            return "I'm sorry, something went wrong while processing your request. Please try again."
    
    def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        try:
            if self.vector_store is None:
                return []
            
            # Search for similar documents
            docs = self.vector_store.similarity_search(query, k=k)
            
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_document_count(self) -> int:
        """Get the number of documents in the knowledge base"""
        try:
            if self.vector_store is None:
                return 0
            
            return len(self.vector_store.index_to_docstore_id)
            
        except Exception as e:
            self.logger.error(f"Error getting document count: {str(e)}")
            return 0
    
    def reload_csv_data(self):
        """Reload CSV data from call.csv file"""
        try:
            self.logger.info("Reloading CSV data...")
            self._load_csv_data()
            self.logger.info("CSV data reloaded successfully")
        except Exception as e:
            self.logger.error(f"Error reloading CSV data: {str(e)}")
    
    def clear_knowledge_base(self):
        """Clear the entire knowledge base"""
        try:
            # Remove vector store files
            if os.path.exists("vector_store"):
                import shutil
                shutil.rmtree("vector_store")
            
            # Clear database
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM documents')
            cursor.execute('DELETE FROM csv_data')
            conn.commit()
            conn.close()
            
            # Reset components
            self.vector_store = None
            self.retrieval_chain = None
            
            self.logger.info("Knowledge base cleared successfully")
            
        except Exception as e:
            self.logger.error(f"Error clearing knowledge base: {str(e)}")
            raise 