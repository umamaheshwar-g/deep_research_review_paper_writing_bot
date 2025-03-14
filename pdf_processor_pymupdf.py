import time
import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from langchain_community.document_loaders import PyMuPDFLoader
import json
import argparse
import glob
import re
import fitz  # PyMuPDF
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from multiprocessing import Pool
import traceback

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

@dataclass
class PDFLoadResult:
    filename: str
    load_time: float
    pages: int
    data: List  # Add data field to store processed content

def extract_metadata_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata directly from PDF content when no search results are available.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        Dict[str, Any]: Extracted metadata
    """
    metadata = {}
    
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Extract text from first few pages (title, authors, abstract are usually here)
        text = ""
        for i in range(min(3, len(doc))):
            text += doc[i].get_text()
        
        # Try to extract title (usually the largest text on first page)
        title_match = re.search(r'^(.+?)(?:\n|$)', text.strip())
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Try to extract authors (often after title, before abstract)
        # This is a simple heuristic and might need refinement
        authors_pattern = r'(?:authors?|by)(?:\s*:|\s+)([^.]+?)(?:\n|$)'
        authors_match = re.search(authors_pattern, text, re.IGNORECASE)
        if authors_match:
            authors_text = authors_match.group(1).strip()
            # Split by common separators
            authors = [a.strip() for a in re.split(r'[,;]|\sand\s', authors_text) if a.strip()]
            if authors:
                metadata['authors'] = authors
        
        # Try to extract abstract
        abstract_pattern = r'(?:abstract|summary)(?:\s*:|\s*—|\s*-|\s+)([^.]+(?:\.[^.]+){1,10})'
        abstract_match = re.search(abstract_pattern, text, re.IGNORECASE)
        if abstract_match:
            metadata['abstract'] = abstract_match.group(1).strip()
        
        # Try to extract DOI
        doi_pattern = r'(?:doi|DOI)(?:\s*:|\s+)(10\.\d{4,}(?:\.\d+)*\/\S+)'
        doi_match = re.search(doi_pattern, text)
        if doi_match:
            metadata['doi'] = doi_match.group(1).strip()
        
        # Extract document info metadata
        doc_info = doc.metadata
        if doc_info:
            if 'title' in doc_info and doc_info['title'] and not metadata.get('title'):
                metadata['title'] = doc_info['title']
            if 'author' in doc_info and doc_info['author'] and not metadata.get('authors'):
                # Split author string into list
                authors = [a.strip() for a in doc_info['author'].split(';')]
                if not authors:
                    authors = [doc_info['author']]
                metadata['authors'] = authors
            if 'subject' in doc_info and doc_info['subject']:
                metadata['abstract'] = doc_info['subject']
            if 'keywords' in doc_info and doc_info['keywords']:
                metadata['keywords'] = [k.strip() for k in doc_info['keywords'].split(',')]
        
        # Close the document
        doc.close()
        
    except Exception as e:
        print(f"Error extracting metadata from PDF: {str(e)}")
    
    return metadata

def find_paper_metadata(local_id: str, uuid_dir: str) -> dict:
    """
    Find paper metadata from smart_results.json file.
    
    Args:
        local_id (str): Local ID of the paper
        uuid_dir (str): Path to the UUID directory
        
    Returns:
        dict: Complete paper metadata without modifications
    """
    try:
        # Extract UUID from path if it's a full path
        if os.path.exists(uuid_dir):
            # If uuid_dir is a file path, get its directory
            if os.path.isfile(uuid_dir):
                uuid_dir = os.path.dirname(uuid_dir)
        
        # Construct path to smart_results.json
        smart_results_path = os.path.join(uuid_dir, "smart_search_results", "smart_results.json")
        
        # Check if file exists
        if not os.path.exists(smart_results_path):
            print(f"No smart_results.json found at {smart_results_path}")
            return None
            
        # Load and parse smart_results.json
        with open(smart_results_path, 'r', encoding='utf-8') as f:
            search_data = json.load(f)
        
        # Get papers list
        papers = search_data.get("papers", [])
        
        # Find matching paper
        for paper in papers:
            if paper.get('local_id') == local_id:
                print(f"Found metadata for paper {local_id}")
                if 'evaluation' in paper:
                    print(f"Evaluation data found: {paper['evaluation']}")
                return paper
                
        print(f"No metadata found for paper {local_id}")
        return None
        
    except Exception as e:
        print(f"Error finding paper metadata: {e}")
        return None

def convert_metadata_to_string(paper_metadata: Dict[str, Any]) -> str:
    """
    Convert paper metadata to a string with stopwords removed.
    
    Args:
        paper_metadata (Dict[str, Any]): Paper metadata dictionary
        
    Returns:
        str: String representation of metadata with stopwords removed
    """
    if not paper_metadata:
        return ""
    
    # No fields to exclude - include everything
    exclude_fields = []  # Empty list to include all fields
    
    # Create a string from all metadata fields
    metadata_str = ""
    for key, value in paper_metadata.items():
        if key not in exclude_fields:
            if isinstance(value, list):
                # Handle list values (like authors)
                if all(isinstance(item, str) for item in value):
                    metadata_str += f"{key}: {' '.join(value)} "
                else:
                    # For complex lists, just use the key
                    metadata_str += f"{key} "
            elif isinstance(value, dict):
                # For dictionaries, include the key and a placeholder
                metadata_str += f"{key}: dict "
            elif value is not None:
                metadata_str += f"{key}: {value} "
    
    # Tokenize and remove stopwords
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(metadata_str.lower())
    filtered_text = [word for word in word_tokens if word.isalnum() and word not in stop_words]
    
    return " ".join(filtered_text)

def save_processed_data(filename: str, data: List, output_folder: Path, uuid_dir: Optional[str] = None, remove_stopwords: bool = False):
    """
    Save processed PDF data to a JSON file.
    
    Args:
        filename: Path to the PDF file
        data: List of document objects from PyMuPDF
        output_folder: Folder to save processed data
        uuid_dir: Path to the UUID directory containing smart_search_results
        remove_stopwords: Not used anymore, kept for backward compatibility
    
    Returns:
        Path to the saved JSON file
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Create output filename
    base_filename = os.path.basename(filename)
    file_stem = os.path.splitext(base_filename)[0]
    processed_name = f"processed_{file_stem}.json"
    output_path = os.path.join(output_folder, processed_name)
    
    # Extract local_id from filename
    local_id = file_stem
    
    # Try to find paper metadata from smart_results.json
    paper_metadata = None
    if uuid_dir:
        paper_metadata = find_paper_metadata(local_id, uuid_dir)
    
    # If no paper metadata found, try to extract from PDF
    if not paper_metadata:
        extracted_metadata = extract_metadata_from_pdf(filename)
        if extracted_metadata:
            paper_metadata = {
                'local_id': local_id,
                'title': extracted_metadata.get('title'),
                'authors': extracted_metadata.get('authors', []),
                'abstract': extracted_metadata.get('abstract'),
                'doi': extracted_metadata.get('doi')
            }
    
    # Since we're processing as single, data will be a list with one item
    doc = data[0]
    
    # Start with the original metadata from PyMuPDF
    metadata_dict = dict(doc.metadata) if hasattr(doc, 'metadata') else {}
    
    # Add local_id
    metadata_dict['local_id'] = local_id
    
    # Add paper metadata if found - store it as is without modifications
    if paper_metadata:
        # Store the entire paper_metadata as a separate field
        metadata_dict['paper_metadata'] = paper_metadata
        
        # Debug print for evaluation field
        if 'evaluation' in paper_metadata:
            print(f"Evaluation field present in paper_metadata: {paper_metadata['evaluation']}")
        else:
            print("Evaluation field not present in paper_metadata")
    
    processed_data = {
        'page_content': doc.page_content,
        'metadata': metadata_dict
    }
    
    # Save the processed data to a JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    return output_path

def load_pdf(args):
    """Load a single PDF file and return timing info"""
    file, output_folder, uuid_dir, remove_stopwords = args
    start_time = time.time()
    try:
        # Change mode to "single" instead of "page"
        loader = PyMuPDFLoader(file, mode="single", extract_tables="markdown", pages_delimiter="\n<<12344567890>>\n")
        data = loader.load()
        end_time = time.time()
        load_time = end_time - start_time
        pages = len(data)  # This will now be 1 since we're loading as single
        
        # Get the filename from the file path
        filename = os.path.basename(file)
        
        # Save processed data
        save_processed_data(file, data, output_folder, uuid_dir, remove_stopwords)
        
        print(f"{load_time:.2f} seconds to load {filename} ({pages} pages)")
        return PDFLoadResult(file, load_time, pages, data)
    except Exception as e:
        print(f"Error processing {os.path.basename(file)}: {str(e)}")
        traceback.print_exc()  # Print the full traceback for debugging
        return PDFLoadResult(file, 0.0, 0, [])

def process_pdfs(pdf_folder, output_folder, search_results_file=None, processes=None, remove_stopwords=True):
    """Process all PDFs in a folder and return timing info"""
    start_time = time.time()
    
    # Get all PDF files in the folder
    pdf_files = list(Path(pdf_folder).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder}")
        return []
    
    print(f"Processing {len(pdf_files)} PDFs...")
    
    # Get the UUID directory from the pdf_folder path
    uuid_dir = os.path.dirname(os.path.abspath(pdf_folder))
    
    # Always look for smart_results.json in the smart_search_results folder
    smart_results_file = os.path.join(uuid_dir, "smart_search_results", "smart_results.json")
    
    if os.path.exists(smart_results_file):
        print(f"Using smart search results file: {smart_results_file}")
        search_results_file = uuid_dir  # Pass the UUID directory instead of the file path
    else:
        print(f"Warning: No smart_results.json found at {smart_results_file}")
        print("Will attempt to extract metadata directly from PDFs.")
        search_results_file = None
    
    # Create arguments list for the worker function
    args = [(str(file), output_folder, search_results_file, remove_stopwords) for file in pdf_files]
    
    # Use Pool instead of ProcessPoolExecutor for better multiprocessing support
    with Pool(processes=processes) as pool:
        results = pool.map(load_pdf, args)
    
    end_time = time.time()
    total_time = end_time - start_time
    total_pages = sum(result.pages for result in results)
    
    print(f"\nProcessed {len(pdf_files)} PDFs ({total_pages} pages) in {total_time:.2f} seconds")
    print(f"Average time per PDF: {total_time/len(pdf_files):.2f} seconds")
    
    return results

def print_summary(results: List[PDFLoadResult]):
    """Print summary of processing results"""
    if not results:
        return
    
    total_time = sum(r.load_time for r in results)
    total_pages = sum(r.pages for r in results)
    avg_time = total_time / len(results)
    
    print("\nProcessing Summary:")
    print("-" * 50)
    print(f"Total PDFs processed: {len(results)}")
    print(f"Total pages processed: {total_pages}")
    print(f"Total processing time: {total_time:.2f} seconds")
    print(f"Average time per PDF: {avg_time:.2f} seconds")
    
    # Sort by processing time to show slowest files
    print("\nSlowest PDFs:")
    sorted_results = sorted(results, key=lambda x: x.load_time, reverse=True)
    for result in sorted_results[:5]:  # Show top 5 slowest
        print(f"{os.path.basename(result.filename)}: {result.load_time:.2f} seconds ({result.pages} pages)")
    
    return {
        'total_pdfs': len(results),
        'total_pages': total_pages,
        'total_time': total_time,
        'avg_time': avg_time
    }

def process_pdf(pdf_path: str, uuid: str):
    """Process a single PDF file and save with metadata."""
    try:
        # Get local_id from filename
        local_id = Path(pdf_path).stem
        
        # Load PDF content
        loader = PyMuPDFLoader(pdf_path, mode="single", extract_tables="markdown", pages_delimiter="\n<<12344567890>>\n")
        data = loader.load()
        
        # Get UUID directory
        uuid_dir = os.path.join("downloads", uuid)
        
        # Get paper metadata
        paper_metadata = find_paper_metadata(local_id, uuid_dir)
        
        # Create metadata dictionary from PyMuPDF metadata
        metadata = dict(data[0].metadata) if hasattr(data[0], 'metadata') else {}
        
        # Add local_id at top level
        metadata['local_id'] = local_id
        
        # Add paper_metadata as a separate field without modifications
        if paper_metadata:
            metadata['paper_metadata'] = paper_metadata
            if 'evaluation' in paper_metadata:
                print(f"Evaluation field present in paper_metadata: {paper_metadata['evaluation']}")
        
        # Create output data
        processed_data = {
            'page_content': data[0].page_content,
            'metadata': metadata
        }
        
        # Create output path
        output_dir = Path("downloads") / uuid / "processed_data"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"processed_{local_id}.json"
        
        # Save processed data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully processed {local_id}")
        
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")

def process_pdfs_in_folder(uuid: str):
    """Process all PDFs in the papers folder for a given UUID."""
    # Get path to papers folder
    papers_dir = Path("downloads") / uuid / "papers"
    
    if not papers_dir.exists():
        print(f"Papers directory not found: {papers_dir}")
        return
    
    # Process each PDF
    for pdf_file in papers_dir.glob("*.pdf"):
        process_pdf(str(pdf_file), uuid)

def main():
    """Main function to process PDFs from command line"""
    parser = argparse.ArgumentParser(description="Process PDFs and add metadata from smart_results.json")
    parser.add_argument("uuid", help="UUID of the search to process")
    args = parser.parse_args()
    
    process_pdfs_in_folder(args.uuid)

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()