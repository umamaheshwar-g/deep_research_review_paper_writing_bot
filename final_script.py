import streamlit as st
import asyncio
import os
import sys
import subprocess
from dotenv import load_dotenv
import io
from contextlib import redirect_stdout

# Load environment variables from .env file
load_dotenv()

import socket
import random
import uuid
import argparse
import json
from typing import Dict, Any, List
import pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
import glob
import time
import openai
from openai import OpenAI

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from research_paper_downloader.fetch_and_download_flow import process_query
from pdf_processor_pymupdf import process_pdfs, print_summary

# Constants for Pinecone integration
CHUNK_SIZE = 600
CHUNK_OVERLAP = 200
BATCH_SIZE = 100
EMBEDDING_MODEL = "text-embedding-3-large"

class StreamToExpander:
    """
    Custom class to redirect stdout to a Streamlit container.
    This allows for real-time display of CrewAI's output.
    """
    def __init__(self, container):
        self.container = container
        self.text = ""
        self.text_area = self.container.empty()
    
    def write(self, text):
        self.text += text
        self.text_area.markdown(f"```\n{self.text}\n```")
    
    def flush(self):
        pass

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
            # 'title': str(paper_metadata.get('title', '')),
            # 'authors': authors,
            # Add evaluation metadata with proper type handling
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

def index_documents_in_pinecone(processed_data_folder: str, namespace: str) -> None:
    """Index processed documents in Pinecone using the chat UUID as namespace."""
    # Initialize Pinecone and OpenAI
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not pinecone_api_key or not openai_api_key:
        raise ValueError("PINECONE_API_KEY or OPENAI_API_KEY not found in environment variables")
        
    pc = pinecone.Pinecone(api_key=pinecone_api_key)
    client = OpenAI(api_key=openai_api_key)
    index = pc.Index("deepresearchreviewbot")
    
    # Load and chunk documents
    documents = load_processed_data(processed_data_folder)
    chunks = chunk_documents(documents)
    
    # Process in batches
    total_chunks = len(chunks)
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
            raise Exception(f"Error getting embeddings from OpenAI: {str(e)}")
        
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
        
        time.sleep(0.5)  # Rate limiting

def query_pinecone(query: str, namespace: str, top_k: int = 5) -> Dict[str, Any]:
    """Query Pinecone index using the specified namespace."""
    # Initialize Pinecone and OpenAI
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not pinecone_api_key or not openai_api_key:
        raise ValueError("PINECONE_API_KEY or OPENAI_API_KEY not found in environment variables")
        
    pc = pinecone.Pinecone(api_key=pinecone_api_key)
    client = OpenAI(api_key=openai_api_key)
    index = pc.Index("deepresearchreviewbot")
    
    # Get query embedding
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=[query]
        )
        query_embedding = response.data[0].embedding
    except Exception as e:
        raise Exception(f"Error getting embedding from OpenAI: {str(e)}")
    
    # Query the index
    response = index.query(
        namespace=namespace,
        vector=query_embedding,
        top_k=top_k,
        include_values=True,
        include_metadata=True
    )
    
    return response

def format_pinecone_results(results: Dict[str, Any]) -> str:
    """Format Pinecone query results for display."""
    if not results or not results.get('matches'):
        return "No results found."
    
    formatted = []
    for i, match in enumerate(results['matches'], 1):
        score = match['score']
        metadata = match['metadata']
        text = match.get('text', '')  # Get the actual text content
        
        result = f"Result {i+1} (Score: {score:.4f}):\n"
        result += f"Document ID: {metadata.get('local_id', 'Unknown')}\n"
        result += f"Source: {metadata.get('fetched_source', 'Unknown')}\n"
        result += f"Total Pages: {metadata.get('total_pages', 'Unknown')}\n"
        result += f"Chunk: {metadata.get('chunk_id', 'Unknown')}/{metadata.get('total_chunks', 'Unknown')}\n"
        
        if text:
            max_length = 300
            if len(text) > max_length:
                text = text[:max_length] + "..."
            result += f"\nSnippet: {text}\n"
        
        formatted.append(result)
    
    return "\n" + "-" * 80 + "\n\n".join(formatted)

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
    # Add Pinecone-related state variables
    if 'pinecone_initialized' not in st.session_state:
        st.session_state.pinecone_initialized = False
    if 'pinecone_indexed' not in st.session_state:
        st.session_state.pinecone_indexed = False
    if 'pinecone_namespace' not in st.session_state:
        st.session_state.pinecone_namespace = None
    if 'processed_dir' not in st.session_state:
        st.session_state.processed_dir = None
    # Add review paper generation state variables
    if 'review_paper_generated' not in st.session_state:
        st.session_state.review_paper_generated = False
    if 'review_paper_path' not in st.session_state:
        st.session_state.review_paper_path = None
    if 'current_query' not in st.session_state:
        st.session_state.current_query = None

def find_available_port(start=8501, end=8599):
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
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    return available_port

def render_sidebar():
    """Render the sidebar with search parameters and settings."""
    with st.sidebar:
        render_session_retrieval()
        st.divider()
        
        # Search Parameters
        st.header("Search Parameters")
        from_date = st.date_input("From Date (Optional)", value=None)
        until_date = st.date_input("Until Date (Optional)", value=None)
        max_results = st.slider("Maximum papers to search", 5, 100, 30, 5)
        
        # Download Settings
        st.header("Download Settings")
        download_mode = st.radio(
            "Download Mode",
            ["Smart Mode (Recommended)", "Full Download Mode"]
        )
        max_concurrent = st.slider("Concurrent downloads", 1, 10, 3)
        retry_failed = st.checkbox("Auto-retry failed downloads", value=True)
        
        if retry_failed:
            max_retries = st.slider("Max retry attempts", 1, 5, 3)
            
    return {
        'from_date': from_date,
        'until_date': until_date,
        'max_results': max_results,
        'download_mode': download_mode,
        'max_concurrent': max_concurrent,
        'retry_failed': retry_failed,
        'max_retries': max_retries if retry_failed else None
    }

def render_session_retrieval():
    """Render the session retrieval section in the sidebar."""
    st.subheader("📋 Retrieve Previous Session")
    uuid_input = st.text_input(
        "Enter Session UUID to retrieve:",
        placeholder="e.g., 123e4567-e89b-12d3-a456-426614174000"
    )
    
    if st.button("Retrieve Session"):
        handle_session_retrieval(uuid_input)

def handle_session_retrieval(uuid_input):
    """Handle the retrieval of a previous session."""
    if not uuid_input:
        st.warning("Please enter a valid UUID.")
        return
        
    st.session_state.chat_id = uuid_input
    session_dir = os.path.join("downloads", uuid_input)
    
    if not os.path.exists(session_dir):
        st.error(f"No session found with UUID: {uuid_input}")
        return
        
    st.success(f"Session found! UUID: {uuid_input}")
    
    # Check for processed data
    processed_dir = os.path.join(session_dir, "processed_data")
    if os.path.exists(processed_dir):
        st.session_state.processed_dir = processed_dir
        
        # Check if this namespace exists in Pinecone
        if st.session_state.pinecone_initialized:
            # Use the new function to check namespace status
            namespace_status = check_pinecone_namespace(uuid_input)
            
            if namespace_status["error"]:
                st.warning(f"Could not verify Pinecone indexing status: {namespace_status['error']}")
                st.session_state.pinecone_indexed = False
                st.session_state.pinecone_namespace = uuid_input
            elif namespace_status["exists"]:
                if namespace_status["vector_count"] > 0:
                    st.session_state.pinecone_indexed = True
                    st.session_state.pinecone_namespace = uuid_input
                    st.info(f"Documents are already indexed in Pinecone. Found {namespace_status['vector_count']} vectors.")
                else:
                    st.session_state.pinecone_indexed = False
                    st.session_state.pinecone_namespace = uuid_input
                    st.warning(f"Namespace exists but contains no vectors. Reindexing recommended.")
            else:
                st.session_state.pinecone_indexed = False
                st.session_state.pinecone_namespace = uuid_input
                st.warning("No documents found in Pinecone. Indexing required.")
        else:
            st.session_state.pinecone_indexed = False
            st.session_state.pinecone_namespace = None
    
    # Check for review papers
    review_papers = [f for f in os.listdir(session_dir) if f.endswith('.md')]
    if review_papers:
        # Use the most recent review paper
        latest_paper = max(review_papers, key=lambda f: os.path.getmtime(os.path.join(session_dir, f)))
        review_paper_path = os.path.join(session_dir, latest_paper)
        st.session_state.review_paper_generated = True
        st.session_state.review_paper_path = review_paper_path
        st.info(f"Found existing review paper: {latest_paper}")
    else:
        st.session_state.review_paper_generated = False
        st.session_state.review_paper_path = None
        
    display_session_info(session_dir)

def display_session_info(session_dir):
    """Display information about the retrieved session."""
    papers_dir = os.path.join(session_dir, "papers")
    processed_dir = os.path.join(session_dir, "processed_data")
    
    paper_count = len([f for f in os.listdir(papers_dir) if f.endswith('.pdf')]) if os.path.exists(papers_dir) else 0
    processed_count = len([f for f in os.listdir(processed_dir) if f.endswith('.json')]) if os.path.exists(processed_dir) else 0
    review_papers = [f for f in os.listdir(session_dir) if f.endswith('.md')] if os.path.exists(session_dir) else []
    review_paper_count = len(review_papers)
    
    st.info(f"Found {paper_count} papers, {processed_count} processed files, and {review_paper_count} review papers.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📂 Open Papers Folder") and os.path.exists(papers_dir):
            os.startfile(papers_dir)
    with col2:
        if st.button("📂 Open Processed Data") and os.path.exists(processed_dir):
            os.startfile(processed_dir)
    with col3:
        if st.button("📂 Open Session Folder") and os.path.exists(session_dir):
            os.startfile(session_dir)
            
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
            
    # Display review papers if they exist
    if review_papers:
        st.subheader("📝 Existing Review Papers")
        for paper in review_papers:
            with st.expander(paper):
                paper_path = os.path.join(session_dir, paper)
                try:
                    with open(paper_path, 'r', encoding='utf-8') as f:
                        paper_content = f.read()
                        preview = paper_content[:500] + "..." if len(paper_content) > 500 else paper_content
                        st.markdown(preview)
                        
                    # Button to set this as the current review paper
                    if st.button(f"View Full Paper: {paper}"):
                        st.session_state.review_paper_generated = True
                        st.session_state.review_paper_path = paper_path
                except Exception as e:
                    st.error(f"Error reading review paper: {e}")

def process_search_results(result):
    """Process and display search results."""
    if not result:
        return
        
    st.success("Successfully processed your query!")
    
    if 'search_results' in result:
        display_papers(result)
        display_download_summary(result)
        process_downloaded_papers(result)

def display_papers(result):
    """Display the found papers in tabs."""
    papers_container = st.container()
    with papers_container:
        st.subheader("📄 Found Papers")
        
        all_tab, downloaded_tab, failed_tab = st.tabs([
            "All Papers", "Downloaded Papers", "Failed Downloads"
        ])
        
        with all_tab:
            display_all_papers(result)
        with downloaded_tab:
            display_downloaded_papers(result)
        with failed_tab:
            display_failed_papers(result)

def display_all_papers(result):
    """Display all papers with their details."""
    for i, paper in enumerate(result['search_results'], 1):
        with st.expander(f"{i}. {paper.get('title', 'Untitled')}"):
            st.write(f"**Authors:** {', '.join(paper.get('authors', ['Unknown']))}")
            st.write(f"**Year:** {paper.get('year', 'N/A')}")
            st.write(f"**Abstract:** {paper.get('abstract', 'No abstract available')}")
            if paper.get('doi'):
                st.write(f"**DOI:** {paper['doi']}")
            
            if paper.get('doi') in result.get('download_results', {}):
                download_result = result['download_results'][paper['doi']]
                if isinstance(download_result, dict):
                    download_path = download_result.get('path')
                    download_status = download_result.get('status', 'Unknown')
                else:
                    download_path = download_result
                    download_status = "Downloaded" if download_path else "Failed"
                
                if download_path:
                    st.write("✅ **Status:** Downloaded successfully")
                    st.write(f"📁 **Saved as:** {os.path.basename(download_path)}")
                else:
                    st.write(f"❌ **Status:** {download_status}")

def display_downloaded_papers(result):
    """Display successfully downloaded papers."""
    if 'download_results' not in result:
        st.info("No papers have been downloaded yet.")
        return
        
    def get_download_path(result_item):
        if isinstance(result_item, dict):
            return result_item.get('path')
        return result_item
    
    successful_papers = [p for p in result['search_results'] 
                      if p.get('doi') in result['download_results'] 
                      and get_download_path(result['download_results'][p['doi']])]

    if not successful_papers:
        st.info("No papers have been downloaded yet.")
        return
        
    for i, paper in enumerate(successful_papers, 1):
        with st.expander(f"{i}. {paper.get('title', 'Untitled')}"):
            download_result = result['download_results'][paper['doi']]
            download_path = get_download_path(download_result)
            st.write(f"📁 **File:** {os.path.basename(download_path)}")
            st.write(f"**Authors:** {', '.join(paper.get('authors', ['Unknown']))}")
            if paper.get('doi'):
                st.write(f"**DOI:** {paper['doi']}")

def display_failed_papers(result):
    """Display papers that failed to download."""
    if 'download_results' not in result:
        st.info("No failed downloads.")
        return
        
    def is_download_failed(result_item):
        if isinstance(result_item, dict):
            return not result_item.get('path')
        return not result_item
    
    failed_papers = [p for p in result['search_results'] 
                   if p.get('doi') in result['download_results'] 
                   and is_download_failed(result['download_results'][p['doi']])]

    if not failed_papers:
        st.info("No failed downloads.")
        return
        
    for i, paper in enumerate(failed_papers, 1):
        with st.expander(f"{i}. {paper.get('title', 'Untitled')}"):
            download_result = result['download_results'][paper['doi']]
            if isinstance(download_result, dict):
                failure_reason = download_result.get('status', 'Unknown error')
                st.write(f"❌ **Status:** {failure_reason}")
            st.write(f"**Authors:** {', '.join(paper.get('authors', ['Unknown']))}")
            if paper.get('doi'):
                st.write(f"**DOI:** {paper['doi']}")

def display_download_summary(result):
    """Display download summary and metrics."""
    if 'download_results' not in result:
        return
    
    summary_container = st.container()
    with summary_container:
        st.subheader("⬇️ Download Summary")
        
        output_dir = os.path.abspath(result['folders']['downloaded_pdfs_dir'])
        actual_downloaded_files = []
        
        if 'actual_downloaded_files' in result and result['actual_downloaded_files']:
            actual_downloaded_files = result['actual_downloaded_files']
        elif os.path.exists(output_dir):
            actual_downloaded_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.pdf')]
        
        total_papers = len(result['search_results'])
        successful_downloads = len(actual_downloaded_files)
        failed_downloads = total_papers - successful_downloads
        success_rate = (successful_downloads / total_papers * 100) if total_papers > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Papers", total_papers)
        with col2:
            st.metric("Successfully Downloaded", successful_downloads)
        with col3:
            st.metric("Failed Downloads", failed_downloads)
        with col4:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        if successful_downloads > 0:
            st.write("Downloaded papers are saved in:")
            st.code(output_dir)
            
            with st.expander("View Downloaded Files"):
                for i, filename in enumerate(actual_downloaded_files, 1):
                    st.write(f"{i}. {filename}")

def process_downloaded_papers(result):
    """Process downloaded PDF files."""
    if not result.get('download_results'):
        return
    
    output_dir = os.path.abspath(result['folders']['downloaded_pdfs_dir'])
    if not os.path.exists(output_dir):
        st.warning(f"Papers folder not found: {output_dir}")
        return
    
    st.subheader("🔄 Processing PDFs")
    with st.spinner("Processing downloaded PDFs..."):
        processed_dir = os.path.join(os.path.dirname(output_dir), "processed_data")
        os.makedirs(processed_dir, exist_ok=True)
        
        # Save search results
        uuid_dir = os.path.dirname(output_dir)
        search_results_file = os.path.join(uuid_dir, "search_results.json")
        if not os.path.exists(search_results_file) and 'search_results' in result:
            with open(search_results_file, 'w', encoding='utf-8') as f:
                json.dump(result['search_results'], f, ensure_ascii=False, indent=2)
        
        actual_pdf_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) 
                          if f.lower().endswith('.pdf')]
        
        if not actual_pdf_files:
            st.warning("No PDF files found in the papers folder.")
            return

    remove_stopwords = st.checkbox("Remove stopwords from paper metadata", value=False)
    
    processing_results = process_pdfs(
        pdf_folder=output_dir,
        output_folder=processed_dir,
        search_results_file=search_results_file,
        processes=3,
        remove_stopwords=remove_stopwords
    )
    
    if not processing_results:
        return
    
    st.session_state.processing_results = processing_results
    summary = print_summary(processing_results)
    
    proc_col1, proc_col2, proc_col3, proc_col4 = st.columns(4)
    with proc_col1:
        st.metric("PDFs Processed", summary['total_pdfs'])
    with proc_col2:
        st.metric("Total Documents", summary['total_pages'])
    with proc_col3:
        st.metric("Processing Time", f"{summary['total_time']:.1f}s")
    with proc_col4:
        st.metric("Avg Time/PDF", f"{summary['avg_time']:.1f}s")
    
    st.write("Processed data is saved in:")
    st.code(processed_dir)
    
    with st.expander("📄 View Processed Files with Local IDs"):
        processed_files_data = []
        for result in processing_results:
            filename = os.path.basename(result.filename)
            local_id = os.path.splitext(filename)[0]
            processed_files_data.append({
                "Filename": os.path.basename(result.filename),
                "Local ID": local_id,
                "Document Size": f"{len(result.data[0].page_content) if result.data else 0:,} chars",
                "Processing Time": f"{result.load_time:.2f}s"
            })
            
        if processed_files_data:
            st.dataframe(processed_files_data)
    
    # Store processed directory in session state for later indexing
    st.session_state.processed_dir = processed_dir

def handle_command_line_args():
    """Handle command line arguments for batch processing."""
    parser = argparse.ArgumentParser(description="Research Paper Finder")
    parser.add_argument("--uuid", help="UUID of the session to retrieve")
    parser.add_argument("--process", action="store_true", help="Process papers for the specified UUID")
    parser.add_argument("--remove-stopwords", action="store_true", default=True, 
                        help="Remove stopwords from paper_metadata (default: True)")
    parser.add_argument("--keep-original", action="store_false", dest="remove_stopwords",
                        help="Keep original metadata without removing stopwords")
    parser.add_argument("--index", action="store_true", help="Index processed papers in Pinecone")
    parser.add_argument("--generate-review", action="store_true", help="Generate a review paper")
    parser.add_argument("--topic", help="Topic for the review paper")
    parser.add_argument("--check-index", action="store_true", help="Check if documents are indexed in Pinecone")
    args = parser.parse_args()
    
    if not args.uuid:
        parser.print_help()
        return
        
    session_dir = os.path.join("downloads", args.uuid)
    if not os.path.exists(session_dir):
        print(f"No session found with UUID: {args.uuid}")
        return
        
    print(f"Session found! UUID: {args.uuid}")
    print(f"Remove stopwords: {args.remove_stopwords}")
    
    papers_dir = os.path.join(session_dir, "papers")
    processed_dir = os.path.join(session_dir, "processed_data")
    
    paper_count = len([f for f in os.listdir(papers_dir) if f.endswith('.pdf')]) if os.path.exists(papers_dir) else 0
    processed_count = len([f for f in os.listdir(processed_dir) if f.endswith('.json')]) if os.path.exists(processed_dir) else 0
    
    print(f"Found {paper_count} papers and {processed_count} processed files.")
    
    # Check if documents are indexed in Pinecone
    if args.check_index or args.generate_review:
        namespace_status = check_pinecone_namespace(args.uuid)
        if namespace_status["error"]:
            print(f"Error checking Pinecone namespace: {namespace_status['error']}")
        elif namespace_status["exists"]:
            if namespace_status["vector_count"] > 0:
                print(f"Documents are already indexed in Pinecone. Found {namespace_status['vector_count']} vectors.")
                is_indexed = True
            else:
                print(f"Namespace exists but contains no vectors. Reindexing recommended.")
                is_indexed = False
        else:
            print("No documents found in Pinecone. Indexing required.")
            is_indexed = False
            
        # If generating a review and not indexed, automatically index
        if args.generate_review and not is_indexed and processed_count > 0:
            print("Indexing documents before generating review paper...")
            args.index = True
    
    if args.process and paper_count > 0:
        print(f"Processing papers for session UUID: {args.uuid}")
        os.makedirs(processed_dir, exist_ok=True)
        
        if os.path.exists(papers_dir):
            pdf_files = [os.path.join(papers_dir, f) for f in os.listdir(papers_dir) if f.lower().endswith('.pdf')]
            if pdf_files:
                results = process_pdfs(
                    pdf_folder=papers_dir,
                    output_folder=processed_dir,
                    processes=None,
                    remove_stopwords=args.remove_stopwords
                )
                print_summary(results)
            else:
                print("No PDF files found in the papers folder.")
        else:
            print(f"Papers folder not found: {papers_dir}")
    
    # Index in Pinecone if requested
    if args.index and processed_count > 0:
        print(f"Indexing processed papers in Pinecone for UUID: {args.uuid}")
        try:
            index_documents_in_pinecone(processed_dir, args.uuid)
            print("Indexing completed successfully!")
        except Exception as e:
            print(f"Error indexing documents: {str(e)}")
    
    # Generate review paper if requested
    if args.generate_review:
        if not args.topic:
            print("Error: --topic is required when using --generate-review")
            return
            
        print(f"\n{'='*80}")
        print(f"🤖 Generating review paper for topic: {args.topic}")
        print(f"{'='*80}\n")
        
        try:
            # Create a sanitized filename
            sanitized_topic = "".join(c if c.isalnum() else "_" for c in args.topic)
            sanitized_topic = sanitized_topic[:50]  # Limit length
            output_filename = f"{sanitized_topic}_{args.uuid}.md"
            output_path = os.path.join(session_dir, output_filename)
            
            # Get the current directory to ensure we have the correct path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            review_crew_dir = os.path.join(current_dir, "review_paper_writing_crew_new")
            
            # Make sure the directory exists
            if not os.path.exists(review_crew_dir):
                print(f"Error: Review paper directory not found at: {review_crew_dir}")
                return
                
            # Get the path to main.py
            main_script = os.path.join(review_crew_dir, "main.py")
            if not os.path.exists(main_script):
                print(f"Error: Review paper script not found at: {main_script}")
                return
            
            # Run the CrewAI script
            cmd = [
                sys.executable,
                "main.py",  # Just use the script name since we'll set the working directory
                "--topic", args.topic,
                "--namespace", args.uuid,
                "--output", os.path.abspath(output_path),  # Use absolute path for output
                "--index-name", "deepresearchreviewbot"
            ]
            
            # Set up environment with UTF-8 encoding for Windows
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["CREWAI_DISABLE_EMOJI"] = "true"  # Disable emojis in CrewAI output
            
            print(f"Running command in directory: {review_crew_dir}")
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
            
            # Display output in real-time with better formatting
            print("\n" + "-"*40 + " OUTPUT " + "-"*40 + "\n")
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            print("\n" + "-"*88 + "\n")
            
            # Get return code
            return_code = process.poll()
            
            if return_code == 0:
                print(f"\n✅ Review paper generated successfully!")
                print(f"📄 Saved to: {output_path}")
                
                # Display a preview of the paper
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        preview_length = min(500, len(content))
                        preview = content[:preview_length] + ("..." if len(content) > preview_length else "")
                    
                    print(f"\n{'='*40} PREVIEW {'='*40}\n")
                    print(preview)
                    print(f"\n{'='*88}\n")
                except Exception as e:
                    print(f"Error reading paper for preview: {str(e)}")
            else:
                error_output = process.stderr.read()
                print(f"\n❌ Error generating review paper. Return code: {return_code}")
                print(f"Error details: {error_output}")
        except Exception as e:
            print(f"Error generating review paper: {str(e)}")
    
    print(f"\nPapers folder: {os.path.abspath(papers_dir)}")
    print(f"Processed data folder: {os.path.abspath(processed_dir)}")
    
    open_folders = input("Open folders? (y/n): ")
    if open_folders.lower() == 'y':
        if os.path.exists(papers_dir):
            os.startfile(papers_dir)
        if os.path.exists(processed_dir):
            os.startfile(processed_dir)
        if os.path.exists(session_dir):
            os.startfile(session_dir)

def main():
    """Main function for the Streamlit app"""
    st.set_page_config(
        page_title="Research Paper Finder",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    available_port = setup_streamlit_config()
    
    # Initialize Pinecone
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        st.error("PINECONE_API_KEY not found in environment variables. Please check your .env file.")
        return
        
    try:
        pc = pinecone.Pinecone(api_key=pinecone_api_key)
        # Just test connection by getting the index
        index = pc.Index("deepresearchreviewbot")
        st.session_state.pinecone_initialized = True
        st.success("Successfully connected to Pinecone!")
    except Exception as e:
        st.error(f"Failed to initialize Pinecone: {str(e)}")
        st.session_state.pinecone_initialized = False
    
    # Check for UUID in URL parameters
    query_params = st.experimental_get_query_params()
    if "uuid" in query_params and query_params["uuid"]:
        uuid_from_url = query_params["uuid"][0]
        if not st.session_state.chat_id or st.session_state.chat_id != uuid_from_url:
            # Only retrieve if not already loaded or different UUID
            handle_session_retrieval(uuid_from_url)
    
    st.title("📚 Research Paper Finder")
    st.markdown(f"""
    This app helps you search and download research papers based on your query.
    *Running on port: {available_port}*
    """)
    
    # Create tabs for different functionality
    tab1, tab2, tab3 = st.tabs(["Search & Process", "Semantic Search", "Generate Review Paper"])
    
    with tab1:
        sidebar_params = render_sidebar()
        search_query = st.text_input(
            "Enter your research query:",
            placeholder="e.g., 'Recent advances in transformer models for natural language processing'"
        )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            search_button = st.button("🔍 Search and Download")
        with col2:
            if st.session_state.is_processing:
                if st.button("⚠️ Cancel Operation"):
                    st.session_state.should_cancel = True
        
        if search_button and search_query:
            # Store the current query in session state
            st.session_state.current_query = search_query
            handle_search(search_query, sidebar_params)
        elif not st.session_state.search_results:
            display_welcome_message()
    
    with tab2:
        st.header("🔍 Semantic Search")
        
        # Add indexing section at the top of semantic search tab
        if hasattr(st.session_state, 'processed_dir') and st.session_state.chat_id:
            st.subheader("📥 Index Documents")
            
            # Add a button to check indexing status
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔍 Check Indexing Status"):
                    namespace_status = check_pinecone_namespace(st.session_state.chat_id)
                    if namespace_status["error"]:
                        st.error(f"Error checking Pinecone namespace: {namespace_status['error']}")
                    elif namespace_status["exists"]:
                        if namespace_status["vector_count"] > 0:
                            st.session_state.pinecone_indexed = True
                            st.session_state.pinecone_namespace = st.session_state.chat_id
                            st.success(f"Documents are indexed in Pinecone. Found {namespace_status['vector_count']} vectors.")
                        else:
                            st.session_state.pinecone_indexed = False
                            st.session_state.pinecone_namespace = st.session_state.chat_id
                            st.warning(f"Namespace exists but contains no vectors. Reindexing recommended.")
                    else:
                        st.session_state.pinecone_indexed = False
                        st.session_state.pinecone_namespace = st.session_state.chat_id
                        st.warning("No documents found in Pinecone. Indexing required.")
            
            with col2:
                if not st.session_state.pinecone_indexed:
                    if st.button("Index Now"):
                        try:
                            with st.spinner("Indexing documents in Pinecone..."):
                                # Use chat_id as namespace
                                namespace = st.session_state.chat_id
                                index_documents_in_pinecone(st.session_state.processed_dir, namespace)
                                st.session_state.pinecone_indexed = True
                                st.session_state.pinecone_namespace = namespace
                                st.success(f"Successfully indexed documents in Pinecone namespace: {namespace}")
                        except Exception as e:
                            st.error(f"Error indexing documents in Pinecone: {str(e)}")
                else:
                    st.success("Documents are indexed and ready to search!")
            
            st.divider()
        
        # Semantic search interface
        if st.session_state.pinecone_indexed:
            semantic_query = st.text_input(
                "Enter your semantic search query:",
                placeholder="e.g., 'What are the key findings about transformer models?'"
            )
            
            top_k = st.slider("Number of results", min_value=1, max_value=20, value=5)
            
            if st.button("🔍 Search Documents") and semantic_query:
                with st.spinner("Searching documents..."):
                    try:
                        results = query_pinecone(
                            query=semantic_query,
                            namespace=st.session_state.pinecone_namespace,
                            top_k=top_k
                        )
                        
                        st.markdown("### Search Results")
                        st.markdown(format_pinecone_results(results))
                    except Exception as e:
                        st.error(f"Error searching documents: {str(e)}")
        else:
            if hasattr(st.session_state, 'processed_dir'):
                st.info("Please index your documents using the button above to enable semantic search.")
            else:
                st.info("Process documents in the Search & Process tab first to enable semantic search.")
    
    with tab3:
        render_review_paper_tab()

def render_review_paper_tab():
    """Render the review paper generation tab."""
    st.header("📝 Generate Review Paper")
    
    # Check if we have indexed documents
    if not st.session_state.pinecone_indexed:
        st.warning("Please index your documents first in the Semantic Search tab before generating a review paper.")
        return
    
    # Display current session info
    if st.session_state.chat_id:
        st.info(f"Current Session UUID: **{st.session_state.chat_id}**")
    
    # Input for review paper topic
    review_topic = st.text_input(
        "Enter the topic for your review paper:",
        value=st.session_state.current_query if st.session_state.current_query else "",
        placeholder="e.g., 'Recent advances in transformer models for natural language processing'"
    )
    
    # Generate button
    col1, col2 = st.columns([1, 1])
    with col1:
        generate_button = st.button("🖋️ Generate New Review Paper")
    
    with col2:
        if st.session_state.review_paper_generated and st.session_state.review_paper_path:
            regenerate_button = st.button("🔄 Regenerate with Same Topic")
    
    # Handle generate button click
    if generate_button and review_topic and st.session_state.chat_id:
        with st.status("🤖 **AI Agents at work...**", state="running", expanded=True) as status:
            with st.container(height=500, border=False):
                output_container = st.container()
                try:
                    generate_review_paper(review_topic, st.session_state.chat_id, output_container)
                    status.update(label="✅ Review Paper Ready!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Error generating review paper: {str(e)}")
                    status.update(label="❌ Error generating review paper", state="error", expanded=True)
    
    # Handle regenerate button click
    if 'regenerate_button' in locals() and regenerate_button and review_topic and st.session_state.chat_id:
        with st.status("🤖 **AI Agents regenerating paper...**", state="running", expanded=True) as status:
            with st.container(height=500, border=False):
                output_container = st.container()
                try:
                    generate_review_paper(review_topic, st.session_state.chat_id, output_container)
                    status.update(label="✅ Review Paper Updated!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Error regenerating review paper: {str(e)}")
                    status.update(label="❌ Error regenerating review paper", state="error", expanded=True)
    
    # Display generated paper if available
    if st.session_state.review_paper_generated and st.session_state.review_paper_path:
        # Display the paper
        try:
            with open(st.session_state.review_paper_path, 'r', encoding='utf-8') as f:
                paper_content = f.read()
            
            # Extract filename for display
            filename = os.path.basename(st.session_state.review_paper_path)
            
            st.subheader(f"📄 Review Paper: {filename}", divider="rainbow")
            
            # Add download and open folder buttons
            col1, col2 = st.columns([1, 1])
            with col1:
                st.download_button(
                    label="⬇️ Download Review Paper",
                    data=paper_content,
                    file_name=filename,
                    mime="text/markdown"
                )
            with col2:
                if st.button("📂 Open Containing Folder"):
                    folder_path = os.path.dirname(st.session_state.review_paper_path)
                    os.startfile(folder_path)
            
            # Display paper content
            st.markdown(paper_content)
                
        except Exception as e:
            st.error(f"Error displaying review paper: {str(e)}")

def generate_review_paper(topic: str, namespace: str, output_container=None):
    """Generate a review paper using the CrewAI system."""
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join("downloads", namespace)
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
            st.error(f"Review paper directory not found at: {review_crew_dir}")
            return
            
        # Get the path to main.py
        main_script = os.path.join(review_crew_dir, "main.py")
        if not os.path.exists(main_script):
            st.error(f"Review paper script not found at: {main_script}")
            return
        
        # Set up the output stream
        if output_container:
            stream_handler = StreamToExpander(output_container)
        
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
        
        print(f"Running command in directory: {review_crew_dir}")
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
        
        # Display output in real-time
        if output_container:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    stream_handler.write(output)
        else:
            # Fallback to simple output collection if no container provided
            output_text = ""
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_text += output
        
        # Get return code
        return_code = process.poll()
        
        if return_code == 0:
            st.session_state.review_paper_generated = True
            st.session_state.review_paper_path = output_path
            st.success(f"Review paper generated successfully!")
        else:
            error_output = process.stderr.read()
            st.error(f"Error generating review paper. Return code: {return_code}")
            st.error(f"Error details: {error_output}")
    except Exception as e:
        st.error(f"Error generating review paper: {str(e)}")
        raise e

def handle_search(query, params):
    """Handle the search and download process."""
    try:
        # Create a new UUID for this search session
        st.session_state.chat_id = str(uuid.uuid4())
        st.session_state.is_processing = True
        st.session_state.should_cancel = False
        
        # Show the UUID immediately
        st.info(f"Session UUID: **{st.session_state.chat_id}**")
        st.write("Save this UUID to retrieve your session later.")
        
        progress_container = st.container()
        with progress_container:
            search_progress = st.progress(0)
            download_progress = st.progress(0)
            status_text = st.empty()
        
        with st.spinner("Processing your request..."):
            result = asyncio.run(execute_search(query, params))
            st.session_state.search_results = result
            process_search_results(result)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        st.session_state.is_processing = False

async def execute_search(query, params):
    """Execute the search with the given parameters."""
    # No need to check for chat_id as it's already set in handle_search
    max_papers = None if params['download_mode'] == "Full Download Mode" else params['max_results']
    
    return await process_query(
        query=query,
        from_date=params['from_date'].strftime("%Y-%m-%d") if params['from_date'] else None,
        until_date=params['until_date'].strftime("%Y-%m-%d") if params['until_date'] else None,
        limit=params['max_results'],
        max_papers=max_papers,
        skip_existing=True,
        max_concurrent=params['max_concurrent'],
        verbose=False,
        return_papers=True,
        chat_id=st.session_state.chat_id,
        base_dir="downloads",
        download_dir_name="papers"
    )

def display_welcome_message():
    """Display the welcome message for new users."""
    st.info("""
    👋 **How to use this app:**
    1. Enter your research query in the search box above
    2. Adjust search and download settings in the sidebar
    3. Click the search button to find and download papers
    4. View results in different tabs and access downloaded files
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        handle_command_line_args()
    else:
        main() 