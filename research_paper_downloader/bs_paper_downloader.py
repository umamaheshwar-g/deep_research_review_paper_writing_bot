"""
Script for downloading research papers using BeautifulSoup from search results JSON files.
"""

import os
import json
import asyncio
import logging
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from tqdm import tqdm
import aiohttp
from .src.utils.bs_downloader import BSDownloader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def download_papers(
    input_file: str = None,
    output_dir: Optional[str] = None,
    max_papers: int = None,
    skip_existing: bool = True,
    max_concurrent: int = 5,
    save_summary_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download papers from a search results JSON file using BeautifulSoup.
    
    Args:
        input_file (str, optional): Path to the search results JSON file. If None, uses the most recent file.
        output_dir (str, optional): Directory to save downloaded papers. If None, creates a timestamped directory.
        max_papers (int, optional): Maximum number of papers to download. If None, downloads all papers.
        skip_existing (bool): Skip papers that already exist.
        max_concurrent (int): Maximum number of concurrent downloads.
        save_summary_to (str, optional): Path to save the download summary JSON. If None, saves in output_dir.
        
    Returns:
        Dict[str, Any]: Summary of download results
    """
    # Use the most recent search results file if not specified
    if not input_file:
        search_results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_results")
        if os.path.exists(search_results_dir):
            # Find the most recent search results file
            files = [os.path.join(search_results_dir, f) for f in os.listdir(search_results_dir) 
                    if f.startswith("search_results_") and f.endswith(".json")]
            if files:
                input_file = max(files, key=os.path.getctime)
                logger.info(f"Using most recent search results file: {os.path.basename(input_file)}")
            else:
                logger.error("No search results files found")
                return {"success": False, "error": "No search results files found"}
        else:
            logger.error(f"Search results directory not found: {search_results_dir}")
            return {"success": False, "error": f"Search results directory not found: {search_results_dir}"}
    
    # Load search results
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        logger.info(f"Loaded {len(papers)} papers from {input_file}")
    except Exception as e:
        logger.error(f"Error loading search results: {str(e)}")
        return {"success": False, "error": str(e)}
    
    # Create output directory if not specified
    if not output_dir:
        # Get base downloads directory
        downloads_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        os.makedirs(downloads_base, exist_ok=True)
        
        # Create timestamped subfolder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(downloads_base, f"bs_download_{timestamp}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Saving papers to: {output_dir}")
    
    # Initialize downloader
    downloader = BSDownloader()
    
    # Limit number of papers if specified
    if max_papers and max_papers < len(papers):
        logger.info(f"Limiting downloads to {max_papers} papers")
        papers = papers[:max_papers]
    
    # Download papers
    logger.info(f"Downloading {len(papers)} papers...")
    
    # Create a semaphore to limit concurrent downloads
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Create download summary with all original paper data
    download_summary = []
    
    async def download_with_semaphore(paper: Dict[str, Any]) -> Dict[str, Any]:
        """Download a single paper with semaphore control and return the result."""
        async with semaphore:
            try:
                # Get paper identifier (DOI, local_id, or title)
                paper_id = paper.get('local_id', paper.get('doi', paper.get('title', 'unknown')))
                
                # Create output filename based on local_id if available, otherwise use DOI or sanitized title
                if paper.get('local_id'):
                    filename = f"{paper['local_id']}.pdf"
                elif paper.get('doi'):
                    filename = f"{paper['doi'].replace('/', '_')}.pdf"
                else:
                    # Use sanitized title if no DOI or local_id
                    title = paper.get('title', 'unknown')
                    # Remove invalid characters from filename
                    filename = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
                    filename = filename[:100] + ".pdf"  # Limit length
                
                output_path = os.path.join(output_dir, filename)
                
                # Create a copy of the paper data for the summary
                result = paper.copy()
                
                # Add download-specific fields
                result['download_status'] = 'skipped' if (skip_existing and os.path.exists(output_path)) else 'pending'
                result['download_path'] = None
                result['downloaded_from'] = None
                
                # Skip if file exists and skip_existing is True
                if skip_existing and os.path.exists(output_path):
                    logger.info(f"File already exists: {output_path}")
                    result['download_path'] = output_path
                    return result
                
                # Download based on source
                source = paper.get('fetched_source', '')
                success = False
                download_source = None
                
                if source == 'semantic_scholar':
                    success = await downloader.download_from_semantic_scholar(paper, output_path)
                    if success:
                        download_source = 'semantic_scholar'
                elif source == 'google_scholar':
                    success = await downloader.download_from_google_scholar(paper, output_path)
                    if success:
                        download_source = 'google_scholar'
                elif source == 'pubmed':
                    success = await downloader.download_from_pubmed(paper, output_path)
                    if success:
                        download_source = 'pubmed'
                elif source == 'crossref':
                    # For crossref, try DOI directly
                    if paper.get('doi'):
                        success = await downloader.download_from_doi(paper['doi'], output_path)
                        if success:
                            download_source = 'doi'
                else:
                    # Try generic approach for unknown sources
                    if paper.get('doi'):
                        success = await downloader.download_from_doi(paper['doi'], output_path)
                        if success:
                            download_source = 'doi'
                    elif paper.get('url'):
                        pdf_url = await downloader.find_pdf_link_from_page(paper['url'])
                        if pdf_url:
                            success = await downloader.download_from_url(pdf_url, output_path)
                            if success:
                                download_source = 'url'
                
                # Update result with download status
                result['download_status'] = 'success' if success else 'failed'
                result['download_path'] = output_path if success else None
                result['downloaded_from'] = download_source
                
                return result
            except Exception as e:
                logger.error(f"Error downloading paper: {str(e)}")
                # Create a copy of the paper data for the summary
                result = paper.copy()
                result['download_status'] = 'error'
                result['download_path'] = None
                result['downloaded_from'] = None
                result['error_message'] = str(e)
                return result
    
    # Create tasks for all downloads
    tasks = [download_with_semaphore(paper) for paper in papers]
    
    # Wait for all downloads to complete
    download_results = await asyncio.gather(*tasks)
    
    # Add results to download summary
    download_summary = download_results
    
    # Count successful downloads
    successful = sum(1 for result in download_summary if result['download_status'] == 'success')
    
    # Verify actual downloaded files in the output directory
    actual_downloaded_files = []
    if os.path.exists(output_dir):
        actual_downloaded_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.pdf')]
    
    # Update download summary based on actual files
    verified_download_summary = []
    for paper in download_summary:
        paper_copy = paper.copy()
        
        # Check if the file actually exists
        if paper['download_status'] == 'success' and paper['download_path']:
            file_exists = os.path.exists(paper['download_path'])
            
            # Update status based on file existence
            if not file_exists:
                paper_copy['download_status'] = 'failed'
                paper_copy['error_message'] = 'File not found on disk'
                paper_copy['download_path'] = None
        
        verified_download_summary.append(paper_copy)
    
    # Count actual successful downloads
    actual_successful = sum(1 for result in verified_download_summary if result['download_status'] == 'success')
    
    # Create summary metadata
    summary_metadata = {
        "total": len(papers),
        "successful": actual_successful,
        "failed": len(papers) - actual_successful,
        "output_dir": output_dir,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_file": input_file
    }
    
    # Create final summary with metadata and results
    final_summary = {
        "metadata": summary_metadata,
        "papers": verified_download_summary
    }
    
    # Save summary to specified path or output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if save_summary_to:
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_summary_to), exist_ok=True)
        summary_path = save_summary_to
    else:
        summary_path = os.path.join(output_dir, f"download_summary_{timestamp}.json")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(final_summary, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\nDownload Summary:")
    print(f"Total papers: {summary_metadata['total']}")
    print(f"Successfully downloaded: {summary_metadata['successful']}")
    print(f"Failed downloads: {summary_metadata['failed']}")
    print(f"Output directory: {summary_metadata['output_dir']}")
    
    # Print details of successful and failed downloads
    if summary_metadata['successful'] > 0:
        print("\nSuccessfully downloaded papers:")
        successful_count = 0
        for paper in verified_download_summary:
            if paper['download_status'] == 'success':
                successful_count += 1
                if successful_count <= 5:  # Show only first 5 for brevity
                    paper_id = paper.get('local_id', paper.get('doi', paper.get('title', 'unknown')))
                    print(f"  - {paper_id} -> {os.path.basename(paper['download_path'])}")
        if successful_count > 5:
            print(f"  ... and {successful_count - 5} more")
    
    if summary_metadata['failed'] > 0:
        print("\nFailed downloads:")
        failed_count = 0
        for paper in verified_download_summary:
            if paper['download_status'] == 'failed' or paper['download_status'] == 'error':
                failed_count += 1
                if failed_count <= 5:  # Show only first 5 for brevity
                    paper_id = paper.get('local_id', paper.get('doi', paper.get('title', 'unknown')))
                    print(f"  - {paper_id}")
        if failed_count > 5:
            print(f"  ... and {failed_count - 5} more")
    
    return final_summary

async def main():
    """
    Main entry point for the script.
    
    This function can be customized with specific parameters as needed.
    For example:
    - To download from a specific file: await download_papers(input_file="path/to/file.json")
    - To limit the number of papers: await download_papers(max_papers=5)
    - To specify an output directory: await download_papers(output_dir="path/to/dir")
    """
    # Use default parameters (most recent search results file, auto-generated output directory)
    return await download_papers()

# Only run the main function if this script is executed directly
if __name__ == "__main__":
    asyncio.run(main()) 