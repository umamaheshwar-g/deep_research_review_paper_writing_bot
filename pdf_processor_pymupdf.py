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

def find_paper_metadata(search_results_file, local_id):
    """Find paper metadata from search results file using only local_id matching."""
    try:
        # If search_results_file is a relative path, convert it to absolute
        if not os.path.isabs(search_results_file):
            search_results_file = os.path.abspath(search_results_file)
        
        # Check if the file exists
        if not os.path.exists(search_results_file):
            # Try looking in the smart_search_results subdirectory
            uuid_dir = os.path.dirname(search_results_file)
            alt_search_results_file = os.path.join(uuid_dir, "smart_search_results", "smart_results.json")
            
            if os.path.exists(alt_search_results_file):
                search_results_file = alt_search_results_file
            else:
                print(f"No search results file found.")
                return None
        
        with open(search_results_file, 'r', encoding='utf-8') as f:
            search_data = json.load(f)
        
        # Get the papers list from smart_results.json
        if isinstance(search_data, dict) and "papers" in search_data:
            search_results = search_data["papers"]
        else:
            search_results = search_data
        
        # Find paper with matching local_id
        for paper in search_results:
            if paper.get('local_id') == local_id:
                return paper
        
        print(f"No metadata found for paper with local_id: {local_id}")
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
    
    # Fields to exclude from the string representation
    exclude_fields = ['local_id', 'source_specific', 'evaluation']
    
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
                # For dictionaries, just use the key
                metadata_str += f"{key} "
            elif value is not None:
                metadata_str += f"{key}: {value} "
    
    # Tokenize and remove stopwords
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(metadata_str.lower())
    filtered_text = [word for word in word_tokens if word.isalnum() and word not in stop_words]
    
    return " ".join(filtered_text)

def save_processed_data(filename: str, data: List, output_folder: Path, search_results_file: Optional[str] = None, remove_stopwords: bool = False):
    """
    Save processed PDF data to a JSON file.
    
    Args:
        filename: Path to the PDF file
        data: List of document objects from PyMuPDF
        output_folder: Folder to save processed data
        search_results_file: Path to search results JSON file for metadata enrichment
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
    
    # Try to find paper metadata from search results
    paper_metadata = None
    if search_results_file:
        paper_metadata = find_paper_metadata(search_results_file, local_id)
    
    # Since we're processing as single, data will be a list with one item
    doc = data[0]
    
    # Start with the original metadata from PyMuPDF
    metadata_dict = dict(doc.metadata) if hasattr(doc, 'metadata') else {}
    
    # Add local_id
    metadata_dict['local_id'] = local_id
    
    # Add paper metadata if found
    if paper_metadata:
        metadata_dict['paper_metadata'] = paper_metadata
    
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
    file, output_folder, search_results_file, remove_stopwords = args
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
        save_processed_data(file, data, output_folder, search_results_file, remove_stopwords)
        
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
    
    # Check if search_results_file exists
    if search_results_file:
        if os.path.exists(search_results_file):
            print(f"Using search results file: {search_results_file}")
        else:
            # Try looking in the smart_search_results subdirectory first
            uuid_dir = os.path.dirname(search_results_file)
            smart_results_file = os.path.join(uuid_dir, "smart_search_results", "smart_results.json")
            
            if os.path.exists(smart_results_file):
                search_results_file = smart_results_file
                print(f"Using smart search results file: {search_results_file}")
            else:
                # Try looking in the search_results subdirectory as fallback
                alt_search_results_file = os.path.join(uuid_dir, "search_results", "search_results.json")
                
                if os.path.exists(alt_search_results_file):
                    search_results_file = alt_search_results_file
                    print(f"Using fallback search results file: {search_results_file}")
                else:
                    print(f"Warning: No search results files found at any location.")
                    print("Will attempt to extract metadata directly from PDFs.")
                    search_results_file = None
    else:
        print("No search results file provided. Will attempt to extract metadata directly from PDFs.")
    
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

def main():
    """Main function to process PDFs from command line"""
    parser = argparse.ArgumentParser(description="Process PDF files using PyMuPDF")
    parser.add_argument("--folder", help="Folder containing PDF files")
    parser.add_argument("--output", help="Output folder for processed data")
    parser.add_argument("--uuid", help="UUID of the search to process")
    parser.add_argument("--processes", type=int, default=None, help="Number of processes to use")
    parser.add_argument("--remove-stopwords", action="store_true", default=True, 
                        help="Remove stopwords from paper_metadata (default: True)")
    parser.add_argument("--keep-original", action="store_false", dest="remove_stopwords",
                        help="Keep original metadata without removing stopwords")
    
    args = parser.parse_args()
    
    folder_path = None
    output_folder = None
    search_results_file = None
    
    if args.uuid:
        # Process PDFs from a specific search UUID
        base_dir = Path("downloads") / args.uuid
        folder_path = base_dir / "papers"
        output_folder = base_dir / "processed_data"
        
        # First try to use smart search results
        smart_results_file = base_dir / "smart_search_results" / "smart_results.json"
        if smart_results_file.exists():
            search_results_file = smart_results_file
            print(f"Using smart search results file: {search_results_file}")
        else:
            # Fall back to regular search results
            search_results_file = base_dir / "search_results.json"
            
            # Ensure the output folder exists
            output_folder.mkdir(exist_ok=True, parents=True)
            
            # Check for search results in alternate locations if needed
            if not search_results_file.exists():
                alt_search_results = base_dir / "search_results" / "search_results.json"
                if alt_search_results.exists():
                    search_results_file = alt_search_results
                    print(f"Using fallback search results file: {search_results_file}")
                else:
                    search_results_file = None
                    print(f"No search results files found: {search_results_file}")
    elif args.folder:
        # Process PDFs from a custom folder
        folder_path = Path(args.folder)
        
        # If output folder is specified, use it; otherwise, create a 'processed_data' folder next to the input folder
        if args.output:
            output_folder = Path(args.output)
        else:
            output_folder = folder_path.parent / "processed_data"
        
        # Ensure the output folder exists
        output_folder.mkdir(exist_ok=True, parents=True)
    else:
        print("Error: Either --uuid or --folder must be specified")
        return []
    
    print(f"Processing PDFs from: {folder_path}")
    print(f"Saving processed data to: {output_folder}")
    print(f"Remove stopwords: {args.remove_stopwords}")
    
    results = process_pdfs(
        pdf_folder=folder_path,
        output_folder=output_folder,
        search_results_file=search_results_file,
        processes=args.processes,
        remove_stopwords=args.remove_stopwords
    )
    
    return results

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()