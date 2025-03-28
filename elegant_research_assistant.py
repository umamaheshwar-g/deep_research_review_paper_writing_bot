import streamlit as st
import asyncio
import os
import sys
import subprocess
import uuid
import json
import time
from datetime import datetime
import glob
from typing import Dict, Any, List, Optional, Tuple
import random
import socket
from dotenv import load_dotenv
from contextlib import redirect_stdout
import io
import traceback
import re

# Load environment variables
load_dotenv()

# Third-party imports
import pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from openai import OpenAI

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import project modules
from research_paper_downloader.fetch_and_download_flow import process_query
from pdf_processor_pymupdf import process_pdfs, print_summary

# Constants
CHUNK_SIZE = 600
CHUNK_OVERLAP = 200
BATCH_SIZE = 100
EMBEDDING_MODEL = "text-embedding-3-large"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Custom CSS for elegant AI styling
CUSTOM_CSS = """
<style>
    /* Base styles */
    .main {
        color: #333333;
    }
    .stTextInput > label, .stSlider > label, .stSelectbox > label {
        color: #333333 !important;
        font-weight: 500;
    }
    .stButton button {
        color: white !important;
    }
    
    /* AI container styling */
    .ai-container {
        border-radius: 10px;
        background: linear-gradient(145deg, #f0f0f0, #e6e6e6);
        box-shadow: 5px 5px 10px #d1d1d1, -5px -5px 10px #ffffff;
        padding: 20px;
        margin: 10px 0;
    }
    .ai-header {
        color: #1E88E5;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .ai-button {
        background: linear-gradient(145deg, #1E88E5, #1976D2);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .ai-button:hover {
        background: linear-gradient(145deg, #1976D2, #1565C0);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .ai-progress {
        margin: 15px 0;
        height: 10px;
        border-radius: 5px;
        background: #f0f0f0;
    }
    .ai-progress-bar {
        height: 100%;
        border-radius: 5px;
        background: linear-gradient(90deg, #1E88E5, #64B5F6);
        transition: width 0.3s ease;
    }
    .ai-card {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 15px;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    .ai-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    .ai-suggestion {
        background-color: #f8f9fa;
        border-left: 3px solid #1E88E5;
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 0 5px 5px 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .ai-suggestion:hover {
        background-color: #e3f2fd;
        transform: translateX(2px);
    }
    .sidebar-status {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        font-size: 0.9em;
    }
    .status-pending {
        background-color: #fff3e0;
        border-left: 3px solid #ff9800;
        color: #333333;
    }
    .status-in-progress {
        background-color: #e3f2fd;
        border-left: 3px solid #2196f3;
        color: #333333;
    }
    .status-complete {
        background-color: #e8f5e9;
        border-left: 3px solid #4caf50;
        color: #333333;
    }
    .status-error {
        background-color: #ffebee;
        border-left: 3px solid #f44336;
        color: #333333;
    }
    
    /* Custom button styling */
    .research-button {
        background: linear-gradient(90deg, #1976D2, #2196F3);
        color: white !important;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 16px;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 10px;
    }
    .research-button:hover {
        background: linear-gradient(90deg, #1565C0, #1976D2);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    .research-button:disabled {
        background: linear-gradient(90deg, #90CAF9, #BBDEFB);
        box-shadow: none;
        cursor: not-allowed;
    }
    
    /* Slider styling */
    .stSlider [data-baseweb="slider"] {
        height: 6px;
    }
    .stSlider [data-baseweb="thumb"] {
        background-color: #1976D2;
        border-color: #1976D2;
    }
</style>
"""

# Stream handler for capturing output
class StreamToSidebar:
    """Custom class to redirect stdout to a Streamlit sidebar container."""
    def __init__(self, container):
        self.container = container
        self.text = ""
        self.text_area = self.container.empty()
    
    def write(self, text):
        self.text += text
        self.text_area.markdown(f"```\n{self.text}\n```")
    
    def flush(self):
        pass 

class StreamToExpander:
    """Custom class to redirect stdout to a Streamlit container."""
    def __init__(self, container):
        self.container = container
        self.text = ""
        self.text_area = self.container.empty()
    
    def write(self, text):
        self.text += text
        self.text_area.markdown(f"```\n{self.text}\n```")
    
    def flush(self):
        pass

def init_session_state():
    """Initialize session state variables."""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'download_status' not in st.session_state:
        st.session_state.download_status = {}
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    if 'should_cancel' not in st.session_state:
        st.session_state.should_cancel = False
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = None
    if 'chat_id' not in st.session_state:
        st.session_state.chat_id = None
    if 'pinecone_initialized' not in st.session_state:
        st.session_state.pinecone_initialized = False
    if 'pinecone_indexed' not in st.session_state:
        st.session_state.pinecone_indexed = False
    if 'pinecone_namespace' not in st.session_state:
        st.session_state.pinecone_namespace = None
    if 'processed_dir' not in st.session_state:
        st.session_state.processed_dir = None
    if 'review_paper_generated' not in st.session_state:
        st.session_state.review_paper_generated = False
    if 'review_paper_path' not in st.session_state:
        st.session_state.review_paper_path = None
    if 'current_query' not in st.session_state:
        st.session_state.current_query = None
    if 'query_suggestions' not in st.session_state:
        st.session_state.query_suggestions = []
    if 'process_status' not in st.session_state:
        st.session_state.process_status = {
            'fetch': {'status': 'pending', 'message': 'Not started'},
            'process': {'status': 'pending', 'message': 'Not started'},
            'index': {'status': 'pending', 'message': 'Not started'},
            'review': {'status': 'pending', 'message': 'Not started'}
        }
    if 'followup_questions' not in st.session_state:
        st.session_state.followup_questions = []
    if 'generate_review_requested' not in st.session_state:
        st.session_state.generate_review_requested = False
    if 'review_topic' not in st.session_state:
        st.session_state.review_topic = None
    if 'last_query' not in st.session_state:
        st.session_state.last_query = None
    if 'selected_suggestion' not in st.session_state:
        st.session_state.selected_suggestion = None
    if 'default_query_value' not in st.session_state:
        st.session_state.default_query_value = ""

def find_available_port(start=8600, end=8699):
    """Find an available port for the Streamlit server."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    return random.randint(9000, 9999)

def setup_streamlit_config():
    """Configure Streamlit server settings."""
    available_port = find_available_port()
    os.environ['STREAMLIT_SERVER_PORT'] = str(available_port)
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '127.0.0.1'  # Use loopback address instead of 'localhost'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    return available_port

def update_process_status(process_name, status, message):
    """Update the process status in the session state."""
    if process_name in st.session_state.process_status:
        st.session_state.process_status[process_name] = {
            'status': status,
            'message': message
        }

def check_pinecone_namespace(namespace: str) -> Dict[str, Any]:
    """
    Check if a namespace exists in Pinecone and has vectors.
    
    Args:
        namespace (str): The namespace to check
        
    Returns:
        Dict with keys:
        - exists (bool): Whether the namespace exists
        - vector_count (int): Number of vectors in the namespace
        - error (str, optional): Error message if any
    """
    result = {
        "exists": False,
        "vector_count": 0,
        "error": None
    }
    
    # If Pinecone is not initialized, return a default result
    # This allows the app to continue in limited mode
    if not st.session_state.pinecone_initialized:
        result["error"] = "Pinecone is not initialized"
        return result
    
    try:
        # Initialize Pinecone
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
            result["error"] = "PINECONE_API_KEY not found in environment variables"
            return result
            
        pc = pinecone.Pinecone(api_key=pinecone_api_key)
        index = pc.Index("deepresearchreviewbot")
        
        # Get index stats
        stats = index.describe_index_stats()
        
        # Check if namespace exists
        if 'namespaces' in stats and namespace in stats['namespaces']:
            result["exists"] = True
            result["vector_count"] = stats['namespaces'][namespace].get('vector_count', 0)
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def generate_query_suggestions(query: str) -> List[str]:
    """
    Generate improved query suggestions using Gemini.
    
    Args:
        query (str): The original user query
        
    Returns:
        List[str]: List of suggested improved queries
    """
    if not GEMINI_API_KEY:
        return [
            f"{query} recent developments",
            f"{query} state of the art",
            f"{query} review"
        ]
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.7,
            streaming=False
        )
        
        prompt = f"""
        I'm searching for research papers on: "{query}"
        
        Please suggest 3 improved versions of this query that would help me find the most relevant and recent research papers.
        Make the suggestions more specific, include relevant technical terms, and ensure they're well-formed for academic search.
        
        Format your response as a numbered list with just the 3 suggestions, nothing else.
        """
        
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        
        # Extract suggestions from the response
        suggestions = []
        for line in response.content.strip().split('\n'):
            # Remove numbering and any extra formatting
            clean_line = line.strip()
            if clean_line:
                # Remove numbering like "1.", "2.", etc.
                if clean_line[0].isdigit() and clean_line[1:].startswith('. '):
                    clean_line = clean_line[3:].strip()
                # Remove other potential markers like "- ", "* ", etc.
                elif clean_line.startswith(('- ', '* ', '• ')):
                    clean_line = clean_line[2:].strip()
                
                if clean_line and clean_line not in suggestions:
                    suggestions.append(clean_line)
        
        # Ensure we have exactly 3 suggestions
        if len(suggestions) < 3:
            # Add generic suggestions if we don't have enough
            default_suggestions = [
                f"{query} recent developments",
                f"{query} state of the art",
                f"{query} review"
            ]
            suggestions.extend(default_suggestions[:(3 - len(suggestions))])
        
        return suggestions[:3]  # Return only the first 3 suggestions
        
    except Exception as e:
        print(f"Error generating query suggestions: {str(e)}")
        # Fallback to basic suggestions
        return [
            f"{query} recent developments",
            f"{query} state of the art",
            f"{query} review"
        ] 

def load_processed_data(processed_data_folder: str) -> List[Dict[str, Any]]:
    """Load all processed PDF data from a folder."""
    processed_files = glob.glob(os.path.join(processed_data_folder, "processed_*.json"))
    
    if not processed_files:
        raise ValueError(f"No processed PDF data found in {processed_data_folder}")
    
    documents = []
    for file_path in processed_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                documents.append(data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return documents

def chunk_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Split documents into chunks for embedding and indexing."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = []
    for doc in documents:
        page_content = doc.get('page_content', '')
        metadata = doc.get('metadata', {})
        
        if not page_content:
            continue
        
        texts = text_splitter.split_text(page_content)
        
        # Extract metadata fields including evaluation data
        paper_metadata = metadata.get('paper_metadata', {})
        evaluation_data = paper_metadata.get('evaluation', {})
        
        # Ensure authors is a list of strings
        authors = paper_metadata.get('authors', [])
        if not isinstance(authors, list):
            authors = []
        authors = [str(author) for author in authors if author is not None]
        
        # Ensure score is a number or convert to 0 if not present/invalid
        score = evaluation_data.get('score')
        if not isinstance(score, (int, float)) or score is None:
            score = 0
        
        # Get citation from evaluation data
        citation = evaluation_data.get('citation', '')
        if not citation or citation == 'None':
            # Try to generate a citation if not present
            title = paper_metadata.get('title', '')
            year = paper_metadata.get('published', paper_metadata.get('year', ''))
            journal = paper_metadata.get('journal', '')
            
            if title and authors:
                author_str = authors[0] if authors else 'Unknown'
                if len(authors) > 1:
                    author_str += ' et al.'
                citation = f"{author_str} ({year}). {title}"
                if journal:
                    citation += f". {journal}"
        
        filtered_metadata = {
            'total_pages': int(metadata.get('total_pages', 0)),
            'fetched_source': str(metadata.get('fetched_source', '')),
            'local_id': str(metadata.get('local_id', '')),
            'score': score,
            'citation': str(citation),
            'reasoning': str(evaluation_data.get('reasoning', ''))
        }
        
        # Split content by page delimiter to get page boundaries
        pages = page_content.split('\n<<12344567890>>\n')
        page_boundaries = []
        current_pos = 0
        
        # Calculate the character position of each page boundary
        for page in pages:
            page_len = len(page) + len('\n<<12344567890>>\n')  # Include delimiter length
            page_boundaries.append((current_pos, current_pos + page_len))
            current_pos += page_len
        
        for i, text in enumerate(texts):
            # Find the start position of this chunk in the original content
            chunk_start = page_content.find(text)
            chunk_end = chunk_start + len(text)
            
            # Find which pages this chunk spans
            page_start = 1
            page_end = 1
            
            for page_num, (page_start_pos, page_end_pos) in enumerate(page_boundaries, 1):
                if chunk_start < page_end_pos:
                    page_start = page_num
                    break
            
            for page_num, (page_start_pos, page_end_pos) in enumerate(page_boundaries, 1):
                if chunk_end <= page_end_pos:
                    page_end = page_num
                    break
            
            chunk = {
                'text': text,
                'metadata': {
                    **filtered_metadata,
                    'chunk_id': i,
                    'total_chunks': len(texts),
                    'page_start': page_start,
                    'page_end': page_end
                }
            }
            chunks.append(chunk)
    
    return chunks

def index_documents_in_pinecone(processed_dir, namespace, sidebar_status_container=None):
    """
    Index processed documents in Pinecone.
    
    Args:
        processed_dir (str): Directory containing processed documents
        namespace (str): Namespace to use in Pinecone
        sidebar_status_container: Optional Streamlit container for status updates
        
    Returns:
        bool: True if indexing was successful, False otherwise
    """
    # If Pinecone is not initialized, skip indexing but return True to allow the process to continue
    if not st.session_state.pinecone_initialized:
        print("Skipping Pinecone indexing (not initialized)")
        if sidebar_status_container:
            sidebar_status_container.info("Skipping Pinecone indexing (not initialized)")
        return True
    
    try:
        # Import necessary functions
        from final_script import load_processed_data, chunk_documents
        import time
        
        # Initialize Pinecone and OpenAI
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not pinecone_api_key or not openai_api_key:
            error_msg = "PINECONE_API_KEY or OPENAI_API_KEY not found in environment variables"
            print(error_msg)
            if sidebar_status_container:
                sidebar_status_container.error(error_msg)
            return False
            
        pc = pinecone.Pinecone(api_key=pinecone_api_key)
        client = OpenAI(api_key=openai_api_key)
        index = pc.Index("deepresearchreviewbot")
        
        # Load and chunk documents
        if sidebar_status_container:
            sidebar_status_container.info("Loading and chunking documents...")
        
        documents = load_processed_data(processed_dir)
        chunks = chunk_documents(documents)
        
        # Process in batches
        BATCH_SIZE = 100
        total_chunks = len(chunks)
        
        if sidebar_status_container:
            sidebar_status_container.info(f"Indexing {total_chunks} chunks in batches of {BATCH_SIZE}...")
        
        for i in range(0, total_chunks, BATCH_SIZE):
            batch = chunks[i:i+BATCH_SIZE]
            
            # Get embeddings for the batch
            texts = [chunk['text'] for chunk in batch]
            try:
                response = client.embeddings.create(
                    model="text-embedding-3-large",
                    input=texts
                )
                embeddings = [embedding.embedding for embedding in response.data]
            except Exception as e:
                error_msg = f"Error getting embeddings from OpenAI: {str(e)}"
                print(error_msg)
                if sidebar_status_container:
                    sidebar_status_container.error(error_msg)
                return False
            
            # Prepare vectors for upsert
            vectors = []
            for idx, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                vectors.append({
                    'id': f"{chunk['metadata']['local_id']}_{chunk['metadata']['chunk_id']}",
                    'values': embedding,
                    'metadata': {
                        **chunk['metadata'],
                        'text': chunk['text']
                    }
                })
            
            # Upsert to Pinecone
            index.upsert(
                vectors=vectors,
                namespace=namespace
            )
            
            # Update progress
            progress = min(100, int((i + len(batch)) / total_chunks * 100))
            if sidebar_status_container:
                sidebar_status_container.info(f"Indexing progress: {progress}% ({i + len(batch)}/{total_chunks} chunks)")
            
            time.sleep(0.5)  # Rate limiting
        
        if sidebar_status_container:
            sidebar_status_container.success(f"Successfully indexed {total_chunks} chunks in Pinecone namespace: {namespace}")
        
        return True
    except Exception as e:
        error_msg = f"Error indexing documents in Pinecone: {str(e)}"
        print(error_msg)
        if sidebar_status_container:
            sidebar_status_container.error(error_msg)
        traceback.print_exc()
        return False

async def process_query(query, sidebar_status_container, research_level=40):
    """
    Process a query to search for papers and download them.
    
    Args:
        query (str): The query to search for
        sidebar_status_container: Streamlit container for status updates
        research_level (int): The number of papers to search for
        
    Returns:
        bool: True if the query was processed successfully, False otherwise
    """
    if not query:
        sidebar_status_container.warning("Please enter a query.")
        return False
    
    # Generate a UUID for this chat session if not already set
    if 'chat_id' not in st.session_state or not st.session_state.chat_id:
        st.session_state.chat_id = str(uuid.uuid4())
    
    chat_id = st.session_state.chat_id
    
    # Create directories for this chat session
    session_dir = os.path.join("downloads", chat_id)
    os.makedirs(session_dir, exist_ok=True)
    
    processed_dir = os.path.join(session_dir, "processed_data")
    os.makedirs(processed_dir, exist_ok=True)
    
    # Set the processed directory in session state
    st.session_state.processed_dir = processed_dir
    
    # Set the namespace for Pinecone
    st.session_state.pinecone_namespace = chat_id
    
    # Reset the Pinecone indexed flag
    st.session_state.pinecone_indexed = False
    
    # Save the current query
    st.session_state.current_query = query
    
    # Update status
    sidebar_status_container.info(f"Processing query: {query}")
    sidebar_status_container.info(f"Session ID: {chat_id}")
    
    try:
        # Import the process_query function from research_paper_downloader
        from research_paper_downloader.fetch_and_download_flow import process_query as fetch_and_download
        
        # Call the process_query function from research_paper_downloader
        sidebar_status_container.info("Searching for papers...")
        search_results = await fetch_and_download(
            query=query,
            limit=research_level,
            max_papers=research_level,
            skip_existing=True,
            max_concurrent=3,
            verbose=False,
            return_papers=True,
            chat_id=chat_id,
            base_dir="downloads",
            download_dir_name="papers"
        )
        
        # Save search results to a file
        search_results_file = os.path.join(session_dir, "search_results.json")
        with open(search_results_file, 'w', encoding='utf-8') as f:
            json.dump(search_results['search_results'], f, ensure_ascii=False, indent=4)
        
        # Update status
        sidebar_status_container.success(f"Found {len(search_results['search_results'])} papers.")
        
        # Process papers
        sidebar_status_container.info("Processing papers...")
        
        # Call the process_pdfs function
        from pdf_processor_pymupdf import process_pdfs
        
        papers_dir = os.path.join(session_dir, "papers")
        if not os.path.exists(papers_dir):
            sidebar_status_container.error(f"No papers directory found at: {papers_dir}")
            return False
            
        processed_papers = process_pdfs(
            pdf_folder=papers_dir,
            output_folder=processed_dir,
            search_results_file=search_results_file,
            processes=3,
            remove_stopwords=False
        )
        
        # Update status
        sidebar_status_container.success(f"Processed {len(processed_papers)} papers.")
        
        # If Pinecone is initialized, proceed with indexing
        if st.session_state.pinecone_initialized:
            # Index documents in Pinecone
            sidebar_status_container.info("Indexing documents in Pinecone...")
            indexing_success = index_documents_in_pinecone(processed_dir, chat_id, sidebar_status_container)
            
            if indexing_success:
                st.session_state.pinecone_indexed = True
                sidebar_status_container.success("Documents indexed in Pinecone successfully.")
            else:
                sidebar_status_container.error("Failed to index documents in Pinecone.")
        else:
            # If Pinecone is not initialized, skip indexing but consider the process successful
            sidebar_status_container.info("Skipping Pinecone indexing (running in limited mode).")
        
        return True
        
    except Exception as e:
        sidebar_status_container.error(f"Error processing query: {str(e)}")
        traceback.print_exc()
        return False

def generate_review_paper(topic: str, namespace: str, sidebar_status_container) -> Dict[str, Any]:
    """
    Generate a review paper on a given topic using documents indexed in Pinecone.
    
    Args:
        topic (str): The topic of the review paper
        namespace (str): The namespace in Pinecone where the documents are indexed
        sidebar_status_container: Streamlit container for status updates
        
    Returns:
        Dict[str, Any]: Results of the review paper generation
    """
    if not topic:
        sidebar_status_container.warning("Please enter a topic for the review paper.")
        return {'success': False, 'error': 'No topic provided'}
    
    if not namespace:
        sidebar_status_container.warning("No namespace provided for document retrieval.")
        return {'success': False, 'error': 'No namespace provided'}
    
    # Check if we're running in limited mode (without Pinecone)
    if not st.session_state.pinecone_initialized:
        sidebar_status_container.info("Generating review paper in limited mode (without Pinecone)...")
        
        # Get the processed directory
        if 'processed_dir' not in st.session_state or not st.session_state.processed_dir:
            sidebar_status_container.error("No processed documents found. Please process a query first.")
            return {'success': False, 'error': 'No processed documents found'}
        
        processed_dir = st.session_state.processed_dir
        
        # Generate a simple review paper without using Pinecone
        try:
            # Sanitize the filename
            sanitized_topic = re.sub(r'[\\/*?:"<>|]', "", topic)
            sanitized_topic = sanitized_topic.replace(' ', '_')
            
            # Create the output path
            session_dir = os.path.dirname(processed_dir)
            output_path = os.path.join(session_dir, f"{sanitized_topic}_review.md")
            
            # Create a status box to show progress
            with st.status("🤖 Generating simple review paper...", expanded=True) as status:
                # Create a container for the output
                output_container = st.container()
                
                # Generate the review paper
                sidebar_status_container.info("Generating simple review paper...")
                generate_simple_review(processed_dir, topic, output_path, sidebar_status_container)
                
                # Update status
                status.update(label="✅ Review paper generated successfully!", state="complete")
            
            # Update session state
            st.session_state.review_paper_generated = True
            st.session_state.review_paper_path = output_path
            
            sidebar_status_container.success("Review paper generated successfully!")
            
            return {
                'success': True,
                'output_path': output_path,
                'limited_mode': True
            }
            
        except Exception as e:
            sidebar_status_container.error(f"Error generating review paper: {str(e)}")
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    # If Pinecone is initialized, proceed with the normal flow
    sidebar_status_container.info("Generating review paper using Pinecone...")
    
    try:
        # Create a status box to show progress
        with st.status("🤖 AI Agents at work generating your review paper...", expanded=True) as status:
            # Create a container for the output
            output_container = st.container()
            
            # Generate the review paper
            output_path = generate_review(
                topic=topic,
                namespace=namespace,
                output_dir=os.path.join("downloads", namespace),
                verbose=False,
                output_container=output_container
            )
            
            # Update status
            status.update(label="✅ Review paper generated successfully!", state="complete")
        
        # Update session state
        st.session_state.review_paper_generated = True
        st.session_state.review_paper_path = output_path
        
        sidebar_status_container.success("Review paper generated successfully!")
        
        return {
            'success': True,
            'output_path': output_path
        }
    except Exception as e:
        sidebar_status_container.error(f"Error generating review paper: {str(e)}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def handle_session_retrieval(uuid_input, sidebar_status_container):
    """
    Handle the retrieval of a previous session.
    
    Args:
        uuid_input (str): The UUID of the session to retrieve
        sidebar_status_container: Streamlit container for status updates
        
    Returns:
        bool: True if session was retrieved successfully, False otherwise
    """
    if not uuid_input:
        sidebar_status_container.warning("Please enter a valid UUID.")
        return False
        
    st.session_state.chat_id = uuid_input
    session_dir = os.path.join("downloads", uuid_input)
    
    if not os.path.exists(session_dir):
        sidebar_status_container.error(f"No session found with UUID: {uuid_input}")
        return False
        
    sidebar_status_container.success(f"Session found! UUID: {uuid_input}")
    
    # Check for processed data
    processed_dir = os.path.join(session_dir, "processed_data")
    if os.path.exists(processed_dir):
        st.session_state.processed_dir = processed_dir
        
        # Check if this namespace exists in Pinecone
        if st.session_state.pinecone_initialized:
            # Use the function to check namespace status
            namespace_status = check_pinecone_namespace(uuid_input)
            
            if namespace_status["error"]:
                sidebar_status_container.warning(f"Could not verify Pinecone indexing status: {namespace_status['error']}")
                st.session_state.pinecone_indexed = False
                st.session_state.pinecone_namespace = uuid_input
            elif namespace_status["exists"]:
                if namespace_status["vector_count"] > 0:
                    st.session_state.pinecone_indexed = True
                    st.session_state.pinecone_namespace = uuid_input
                    sidebar_status_container.info(f"Documents are already indexed in Pinecone. Found {namespace_status['vector_count']} vectors.")
                else:
                    st.session_state.pinecone_indexed = False
                    st.session_state.pinecone_namespace = uuid_input
                    sidebar_status_container.warning(f"Namespace exists but contains no vectors. Reindexing recommended.")
            else:
                st.session_state.pinecone_indexed = False
                st.session_state.pinecone_namespace = uuid_input
                sidebar_status_container.warning("No documents found in Pinecone. Indexing required.")
        else:
            # If Pinecone is not initialized, we'll operate in limited mode
            st.session_state.pinecone_indexed = False
            st.session_state.pinecone_namespace = uuid_input
            sidebar_status_container.info("Running in limited mode without Pinecone. Some features may not be available.")
    
    # Check for review papers
    review_papers = [f for f in os.listdir(session_dir) if f.endswith('.md')]
    if review_papers:
        # Use the most recent review paper
        latest_paper = max(review_papers, key=lambda f: os.path.getmtime(os.path.join(session_dir, f)))
        review_paper_path = os.path.join(session_dir, latest_paper)
        st.session_state.review_paper_generated = True
        st.session_state.review_paper_path = review_paper_path
        sidebar_status_container.info(f"Found existing review paper: {latest_paper}")
    else:
        st.session_state.review_paper_generated = False
        st.session_state.review_paper_path = None
    
    # Display search results file if it exists
    search_results_file = os.path.join(session_dir, "search_results.json")
    if os.path.exists(search_results_file):
        try:
            with open(search_results_file, 'r', encoding='utf-8') as f:
                search_results = json.load(f)
                
            if search_results:
                # Extract the query from the first paper's title or abstract
                if isinstance(search_results, list) and len(search_results) > 0:
                    first_paper = search_results[0]
                    if 'title' in first_paper:
                        # Use the title as a fallback for the query
                        st.session_state.current_query = first_paper['title']
        except Exception as e:
            print(f"Error loading search results: {e}")
    
    return True

def open_folder(folder_path):
    """
    Open a folder in the file explorer in a cross-platform way.
    
    Args:
        folder_path (str): Path to the folder to open
    """
    try:
        if sys.platform == 'win32':
            # Windows
            os.startfile(folder_path)
        elif sys.platform == 'darwin':
            # macOS
            subprocess.run(['open', folder_path], check=True)
        else:
            # Linux
            subprocess.run(['xdg-open', folder_path], check=True)
    except Exception as e:
        print(f"Error opening folder: {str(e)}")

def handle_complete_process(query, sidebar_status_container, research_level=60):
    """
    Handle the complete process of searching, downloading, processing, indexing, and generating a review paper.
    
    Args:
        query (str): The query to search for
        sidebar_status_container: Streamlit container for status updates
        research_level (int): The number of papers to search for
        
    Returns:
        bool: True if the process was completed successfully, False otherwise
    """
    if not query:
        sidebar_status_container.warning("Please enter a query.")
        return False
    
    # Set processing flag
    st.session_state.is_processing = True
    
    try:
        # Process the query
        sidebar_status_container.info("Processing query...")
        
        # Create a new event loop for asyncio.run
        try:
            result = asyncio.run(process_query(
                query=query,
                sidebar_status_container=sidebar_status_container,
                research_level=research_level
            ))
        except RuntimeError as e:
            # If there's already an event loop running, use it
            if "There is no current event loop in thread" in str(e):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(process_query(
                        query=query,
                        sidebar_status_container=sidebar_status_container,
                        research_level=research_level
                    ))
                    
                    if result:
                        st.success("Query processed successfully!")
                    else:
                        st.error("Failed to process query.")
                finally:
                    loop.close()
            else:
                raise
        
        if not result:
            sidebar_status_container.error("Failed to process query.")
            st.session_state.is_processing = False
            return False
        
        # Generate a review paper
        sidebar_status_container.info("Generating review paper...")
        
        # Get the chat ID
        chat_id = st.session_state.chat_id
        
        # Generate the review paper
        if st.session_state.pinecone_indexed or not st.session_state.pinecone_initialized:
            # If documents are indexed in Pinecone or we're running in limited mode
            # Sanitize the filename
            sanitized_query = re.sub(r'[\\/*?:"<>|]', "", query)
            sanitized_query = sanitized_query.replace(' ', '_')
            
            # Create the output path
            session_dir = os.path.join("downloads", chat_id)
            output_path = os.path.join(session_dir, f"{sanitized_query}_review.md")
            
            if st.session_state.pinecone_initialized and st.session_state.pinecone_indexed:
                # Generate review paper using Pinecone
                review_result = generate_review_paper(
                    topic=query,
                    namespace=chat_id,
                    sidebar_status_container=sidebar_status_container
                )
            else:
                # Generate a simple review paper without using Pinecone
                review_result = generate_review_paper(
                    topic=query,
                    namespace=chat_id,
                    sidebar_status_container=sidebar_status_container
                )
            
            if review_result['success']:
                sidebar_status_container.success("Review paper generated successfully!")
                st.session_state.review_paper_generated = True
                st.session_state.review_paper_path = review_result['output_path']
            else:
                sidebar_status_container.error(f"Failed to generate review paper: {review_result.get('error', 'Unknown error')}")
                st.session_state.is_processing = False
                return False
        else:
            sidebar_status_container.warning("Documents not indexed in Pinecone. Please index documents first.")
            st.session_state.is_processing = False
            return False
        
        # Set processing flag to False
        st.session_state.is_processing = False
        return True
        
    except Exception as e:
        sidebar_status_container.error(f"Error in complete process: {str(e)}")
        traceback.print_exc()
        st.session_state.is_processing = False
        return False

def generate_simple_review(processed_dir, topic, output_path, sidebar_status_container):
    """
    Generate a simple review paper from processed documents without using Pinecone.
    
    Args:
        processed_dir (str): Directory containing processed documents
        topic (str): The topic of the review paper
        output_path (str): Path to save the review paper
        sidebar_status_container: Streamlit container for status updates
        
    Returns:
        None
    """
    # Check if the processed directory exists
    if not os.path.exists(processed_dir):
        sidebar_status_container.error(f"Processed directory not found: {processed_dir}")
        raise FileNotFoundError(f"Processed directory not found: {processed_dir}")
    
    # Get all JSON files in the processed directory
    json_files = [f for f in os.listdir(processed_dir) if f.endswith('.json')]
    
    if not json_files:
        sidebar_status_container.error("No processed documents found.")
        raise FileNotFoundError("No processed documents found.")
    
    sidebar_status_container.info(f"Found {len(json_files)} processed documents.")
    
    # Load all documents
    documents = []
    for json_file in json_files:
        try:
            with open(os.path.join(processed_dir, json_file), 'r', encoding='utf-8') as f:
                doc = json.load(f)
                documents.append(doc)
        except Exception as e:
            sidebar_status_container.warning(f"Error loading document {json_file}: {str(e)}")
    
    if not documents:
        sidebar_status_container.error("No documents could be loaded.")
        raise ValueError("No documents could be loaded.")
    
    sidebar_status_container.info(f"Successfully loaded {len(documents)} documents.")
    
    # Extract metadata and content from documents
    paper_data = []
    for doc in documents:
        paper_info = {
            'title': doc.get('title', 'Unknown Title'),
            'authors': doc.get('authors', []),
            'year': doc.get('year', 'Unknown Year'),
            'abstract': doc.get('abstract', ''),
            'summary': doc.get('summary', ''),
            'content': doc.get('content', '')
        }
        paper_data.append(paper_info)
    
    # Sort papers by year (if available)
    paper_data.sort(key=lambda x: x['year'] if isinstance(x['year'], int) else 9999, reverse=True)
    
    # Generate the review paper
    sidebar_status_container.info("Generating review paper content...")
    
    # Format the review paper
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Create the review paper content
    review_content = f"""# Literature Review: {topic}

*Generated on: {current_date}*

## Introduction

This literature review explores the topic of "{topic}" based on a collection of {len(paper_data)} research papers. The review aims to synthesize the current state of knowledge, identify key findings, and highlight areas for future research.

## Paper Summaries

"""
    
    # Add paper summaries
    for i, paper in enumerate(paper_data, 1):
        authors_str = ", ".join(paper['authors']) if paper['authors'] else "Unknown Authors"
        year_str = str(paper['year']) if paper['year'] != 'Unknown Year' else 'Unknown Year'
        
        review_content += f"### {i}. {paper['title']}\n\n"
        review_content += f"**Authors:** {authors_str}  \n"
        review_content += f"**Year:** {year_str}  \n\n"
        
        if paper['abstract']:
            review_content += f"**Abstract:**  \n{paper['abstract']}\n\n"
        
        if paper['summary']:
            review_content += f"**Summary:**  \n{paper['summary']}\n\n"
    
    # Add conclusion
    review_content += """## Conclusion

This literature review has presented a summary of research papers related to the specified topic. The papers collectively provide insights into various aspects of the subject, including methodologies, findings, and implications. Future research could build upon these findings to address gaps in the current literature and explore new directions.

## References

"""
    
    # Add references
    for i, paper in enumerate(paper_data, 1):
        authors_str = ", ".join(paper['authors']) if paper['authors'] else "Unknown Authors"
        year_str = str(paper['year']) if paper['year'] != 'Unknown Year' else 'Unknown Year'
        
        review_content += f"{i}. {authors_str} ({year_str}). {paper['title']}.\n\n"
    
    # Save the review paper
    sidebar_status_container.info(f"Saving review paper to {output_path}...")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(review_content)
        
        sidebar_status_container.success(f"Review paper saved to {output_path}")
    except Exception as e:
        sidebar_status_container.error(f"Error saving review paper: {str(e)}")
        raise

def get_working_pinecone_api_key():
    """
    Try to get a working Pinecone API key from different sources.
    
    Returns:
        str: A working Pinecone API key or None if not found
    """
    # First try from environment variable
    api_key = os.getenv("PINECONE_API_KEY")
    
    # If the environment variable key works, return it
    if api_key and test_pinecone_api_key(api_key):
        return api_key
        
    return None

def test_pinecone_api_key(api_key):
    """
    Test if a Pinecone API key is valid.
    
    Args:
        api_key (str): The API key to test
        
    Returns:
        bool: True if the key is valid, False otherwise
    """
    if not api_key:
        return False
        
    try:
        pc = pinecone.Pinecone(api_key=api_key)
        # Just test connection by getting the index
        index = pc.Index("deepresearchreviewbot")
        return True
    except Exception as e:
        print(f"API key test failed: {str(e)}")
        return False

def initialize_pinecone():
    """Initialize Pinecone with API key if available."""
    try:
        # Try to get a working Pinecone API key
        api_key = get_working_pinecone_api_key()
        
        if api_key:
            # Initialize Pinecone using the new API
            pc = pinecone.Pinecone(api_key=api_key)
            # Test connection by getting the index
            index = pc.Index("deepresearchreviewbot")
            st.session_state.pinecone_initialized = True
            print("Pinecone initialized successfully.")
        else:
            # If no API key is available, set the flag to False
            st.session_state.pinecone_initialized = False
            print("Pinecone initialization skipped (no API key).")
    except Exception as e:
        # If there's an error, set the flag to False
        st.session_state.pinecone_initialized = False
        print(f"Error initializing Pinecone: {str(e)}")

def render_sidebar():
    """Render the sidebar with status updates and session retrieval."""
    with st.sidebar:
        # Add logo/header
        st.header("🧠 AI Research")
        st.caption("Research Assistant Dashboard")
        
        st.subheader("Session Management")
        
        # Session retrieval
        uuid_input = st.text_input(
            "Enter Session UUID to retrieve:",
            placeholder="e.g., 123e4567-e89b-12d3-a456-426614174000",
            key="uuid_input"
        )
        
        # Retrieve button
        if st.button("🔄 Retrieve Session", key="retrieve_button_clicked"):
            handle_session_retrieval(uuid_input, st.sidebar)
        
        # Add direct review paper generation option if a session is loaded
        if st.session_state.chat_id and st.session_state.processed_dir:
            st.divider()
            st.subheader("Quick Actions")
            
            # Input for review paper topic
            review_topic = st.text_input(
                "Review Paper Topic:",
                value=st.session_state.current_query if st.session_state.current_query else "",
                placeholder="Enter topic for review paper",
                key="sidebar_review_topic"
            )
            
            # Generate review paper button
            if st.button("📝 Generate Review Paper", key="sidebar_generate_review"):
                if review_topic:
                    st.session_state.is_processing = True
                    
                    # Generate the review paper in the main area
                    # We'll use st.rerun() to trigger the main UI to show the status box
                    st.session_state.generate_review_requested = True
                    st.session_state.review_topic = review_topic
                    st.rerun()
                else:
                    st.sidebar.warning("Please enter a topic for the review paper.")
        
        st.divider()
        
        # Process status
        st.subheader("Process Status")
        status_container = st.container()
        
        # Display current status
        with status_container:
            for process, status_data in st.session_state.process_status.items():
                status = status_data['status']
                message = status_data['message']
                
                if status == 'pending':
                    st.info(f"⏳ {process.capitalize()}: {message}")
                elif status == 'in_progress':
                    st.info(f"🔄 {process.capitalize()}: {message}")
                elif status == 'complete':
                    st.success(f"✅ {process.capitalize()}: {message}")
                elif status == 'error':
                    st.error(f"❌ {process.capitalize()}: {message}")
        
        # Add some space
        st.divider()
        
        # Display session info if available
        if st.session_state.chat_id:
            st.subheader("Current Session")
            
            # Display UUID
            st.code(st.session_state.chat_id, language="")
            
            # Display folder paths
            if st.session_state.processed_dir:
                if st.button("📂 Open Data Folder", key="open_folder_button_clicked"):
                    open_folder(os.path.dirname(st.session_state.processed_dir))
        
        # Add footer
        st.divider()
        st.caption("AI Research Assistant")
        st.caption("Powered by LangChain & Streamlit")
        
        return status_container

def display_review_paper():
    """Display the generated review paper."""
    try:
        if not st.session_state.review_paper_path or not os.path.exists(st.session_state.review_paper_path):
            st.error("Review paper not found. Please generate a review paper first.")
            return
            
        with open(st.session_state.review_paper_path, 'r', encoding='utf-8') as f:
            paper_content = f.read()
        
        # Extract filename for display
        filename = os.path.basename(st.session_state.review_paper_path)
        
        st.header("📄 Research Review")
        st.caption("Generated based on your research topic")
        
        # Add download and regenerate buttons
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.download_button(
                label="⬇️ Download Review Paper",
                data=paper_content,
                file_name=filename,
                mime="text/markdown",
                use_container_width=True
            )
            
        with col2:
            if st.button("🔄 Regenerate with Same Topic", use_container_width=True):
                st.session_state.is_processing = True
                handle_complete_process(st.session_state.current_query, st.sidebar)
                st.session_state.is_processing = False
                st.rerun()
        
        # Add a text area for follow-up questions
        st.subheader("Refine Your Research Review")
        
        followup_question = st.text_input(
            "Ask a follow-up question to refine the review:",
            placeholder="e.g., 'Focus more on applications in healthcare' or 'Expand the section on limitations'",
            key="followup_input"
        )
        
        if followup_question:
            if st.button("🔄 Regenerate with Follow-up", use_container_width=True):
                combined_query = f"{st.session_state.current_query} - {followup_question}"
                st.session_state.is_processing = True
                handle_complete_process(combined_query, st.sidebar)
                st.session_state.is_processing = False
                st.rerun()
        
        # Display paper content
        st.divider()
        
        # Use st.markdown to properly render the markdown content
        st.markdown(paper_content)
        
    except Exception as e:
        st.error(f"Error displaying review paper: {str(e)}")
        traceback.print_exc()

def generate_review(topic: str, namespace: str, output_dir: str, verbose: bool = False, output_container=None) -> str:
    """
    Generate a review paper using the CrewAI system.
    
    Args:
        topic (str): The topic of the review paper
        namespace (str): The namespace in Pinecone where the documents are indexed
        output_dir (str): Directory to save the review paper
        verbose (bool): Whether to print verbose output
        output_container: Optional Streamlit container to display progress
        
    Returns:
        str: Path to the generated review paper
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a sanitized filename
        sanitized_topic = "".join(c if c.isalnum() else "_" for c in topic)
        sanitized_topic = sanitized_topic[:50]  # Limit length
        output_filename = f"{sanitized_topic}_{namespace}.md"
        output_path = os.path.join(output_dir, output_filename)
        
        # Get the current directory to ensure we have the correct path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        review_crew_dir = os.path.join(current_dir, "review_paper_writing_crew_new")
        
        # Make sure the directory exists
        if not os.path.exists(review_crew_dir):
            print(f"Review paper directory not found at: {review_crew_dir}")
            raise FileNotFoundError(f"Review paper directory not found at: {review_crew_dir}")
            
        # Get the path to main.py
        main_script = os.path.join(review_crew_dir, "main.py")
        if not os.path.exists(main_script):
            print(f"Review paper script not found at: {main_script}")
            raise FileNotFoundError(f"Review paper script not found at: {main_script}")
        
        # Run the CrewAI script
        cmd = [
            sys.executable,
            "main.py",  # Just use the script name since we'll set the working directory
            "--topic", topic,
            "--namespace", namespace,
            "--output", os.path.abspath(output_path),  # Use absolute path for output
            "--index-name", "deepresearchreviewbot"
        ]
        
        # Set up environment with UTF-8 encoding for Windows
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["CREWAI_DISABLE_EMOJI"] = "true"  # Disable emojis in CrewAI output
        
        if verbose:
            print(f"Running command in directory: {review_crew_dir}")
        
        # Set up the stream handler if output_container is provided
        stream_handler = None
        if output_container:
            stream_handler = StreamToExpander(output_container)
            
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=review_crew_dir,  # Set the working directory to the review crew directory
            env=env,  # Pass the environment with UTF-8 encoding
            encoding='utf-8',  # Explicitly set encoding for subprocess
            errors='replace'  # Replace any characters that can't be decoded
        )
        
        # Collect output
        output_text = ""
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output_text += output
                if stream_handler:
                    stream_handler.write(output)
                elif verbose:
                    print(output.strip())
        
        # Get return code
        return_code = process.poll()
        
        if return_code == 0:
            if verbose:
                print(f"Review paper generated successfully at: {output_path}")
            return output_path
        else:
            error_output = process.stderr.read()
            error_msg = f"Error generating review paper. Return code: {return_code}. Error details: {error_output}"
            print(error_msg)
            if stream_handler:
                stream_handler.write(f"\n\nERROR: {error_msg}")
            raise RuntimeError(error_msg)
            
    except Exception as e:
        print(f"Error generating review paper: {str(e)}")
        if stream_handler:
            stream_handler.write(f"\n\nERROR: {str(e)}")
        raise

def main():
    """
    Main function to run the Streamlit app.
    """
    try:
        # Set page config with a specific port
        st.set_page_config(
            page_title="AI Research Assistant",
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state variables
        init_session_state()
        
        # Initialize Pinecone with fallback mechanism
        initialize_pinecone()
        
        # Render the sidebar and get the status container
        status_container = render_sidebar()
        
        # Main content area
        st.title("AI Research Assistant")
        
        # Check if review paper generation was requested from sidebar
        if 'generate_review_requested' in st.session_state and st.session_state.generate_review_requested:
            # Clear the flag
            st.session_state.generate_review_requested = False
            
            # Get the topic
            review_topic = st.session_state.review_topic
            
            # Generate the review paper
            review_result = generate_review_paper(
                topic=review_topic,
                namespace=st.session_state.chat_id,
                sidebar_status_container=status_container
            )
            
            if review_result['success']:
                st.success("Review paper generated successfully!")
                st.session_state.review_paper_generated = True
                st.session_state.review_paper_path = review_result['output_path']
                # Display the review paper
                display_review_paper()
            else:
                st.error(f"Failed to generate review paper: {review_result.get('error', 'Unknown error')}")
            
            st.session_state.is_processing = False
        
        # Set default query value if a suggestion was selected
        default_query = ""
        if st.session_state.selected_suggestion is not None:
            default_query = st.session_state.selected_suggestion
            # Reset the selected suggestion
            st.session_state.selected_suggestion = None
        elif 'default_query_value' in st.session_state:
            default_query = st.session_state.default_query_value
        
        # Query input
        query = st.text_input("Enter your research query:", key="query_input", help="Enter a topic to research", value=default_query)
        
        # Save the current query value for next run
        st.session_state.default_query_value = query
        
        # Generate query suggestions if a query is entered
        if query and query != st.session_state.get('last_query', ''):
            st.session_state.last_query = query
            st.session_state.query_suggestions = generate_query_suggestions(query)
        
        # Display query suggestions if available
        if query and 'query_suggestions' in st.session_state and st.session_state.query_suggestions:
            st.subheader("Suggested Queries:")
            suggestion_cols = st.columns(len(st.session_state.query_suggestions))
            
            for i, suggestion in enumerate(st.session_state.query_suggestions):
                with suggestion_cols[i]:
                    if st.button(f"🔍 {suggestion}", key=f"suggestion_{i}"):
                        # Store the suggestion in session state for next run
                        st.session_state.selected_suggestion = suggestion
                        st.rerun()
        
        # Create a container for the buttons
        button_container = st.container()
        
        # Create a row with two columns for the buttons
        col1, col2 = button_container.columns([1, 1])
        
        # Define research level
        research_level = 60  # Default research level
        
        # Add the Write Research Review button to the first column
        if col1.button("Write Research Review", key="write_review_button", 
                      help="Process the query and generate a research review paper",
                      use_container_width=True):
            if not query:
                st.warning("Please enter a query first.")
            else:
                # Set processing flag
                st.session_state.is_processing = True
                
                # Process the query and generate a review paper
                success = handle_complete_process(query, status_container, research_level)
                
                if success:
                    # Display the review paper
                    display_review_paper()
        
        # Add a button for processing only (without generating a review)
        if col2.button("Process Query Only", key="process_query_button", 
                      help="Process the query without generating a review paper",
                      use_container_width=True,
                      type="secondary"):
            if not query:
                st.warning("Please enter a query first.")
            else:
                # Set processing flag
                st.session_state.is_processing = True
                
                # Create a new event loop for asyncio.run
                try:
                    result = asyncio.run(process_query(
                        query=query,
                        sidebar_status_container=status_container,
                        research_level=research_level
                    ))
                    
                    if result:
                        st.success("Query processed successfully!")
                    else:
                        st.error("Failed to process query.")
                except RuntimeError as e:
                    # If there's already an event loop running, use it
                    if "There is no current event loop in thread" in str(e):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(process_query(
                                query=query,
                                sidebar_status_container=status_container,
                                research_level=research_level
                            ))
                            
                            if result:
                                st.success("Query processed successfully!")
                            else:
                                st.error("Failed to process query.")
                        finally:
                            loop.close()
                    else:
                        st.error(f"Error processing query: {str(e)}")
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")
                
                # Set processing flag to False
                st.session_state.is_processing = False
        
        # Display the review paper if it has been generated
        if st.session_state.review_paper_generated and st.session_state.review_paper_path:
            display_review_paper()
        
        # Display a spinner while processing
        if st.session_state.is_processing:
            with st.spinner("Processing..."):
                # This is just a placeholder for the spinner
                # The actual processing is done in the button click handlers
                pass
                
    except Exception as e:
        st.error(f"Error starting the application: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    # Set environment variables for Streamlit
    os.environ['STREAMLIT_SERVER_PORT'] = '9501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    main() 