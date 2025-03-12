import asyncio
import os
import uuid
import json
from datetime import datetime
from .search_papers import search_papers
from .bs_paper_downloader import download_papers
import re
from typing import Dict, List, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Load environment variables
load_dotenv()

# Constants
BATCH_SIZE = 10
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_chat_id(prefix="chat", use_timestamp=True):
    """
    Generate a unique chat ID for the query session
    
    Args:
        prefix (str): Prefix for the chat ID
        use_timestamp (bool): Whether to include timestamp in the chat ID
        
    Returns:
        str: Unique chat ID
    """
    unique_id = uuid.uuid4().hex[:10]
    if use_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{unique_id}_{timestamp}"
    else:
        return f"{prefix}_{unique_id}"

def create_folder_structure(chat_id, base_dir="file_downloads", 
                           search_dir_name="search_results", 
                           smart_search_dir_name="smart_search_results",
                           download_dir_name="downloaded_pdfs", 
                           summary_dir_name="download_summary"):
    """
    Create folder structure for organizing search results and downloads.
    
    Args:
        chat_id (str): Unique identifier for this chat/query
        base_dir (str): Base directory for file downloads
        search_dir_name (str): Name of the search results directory
        smart_search_dir_name (str): Name of the smart search results directory
        download_dir_name (str): Name of the downloaded PDFs directory
        summary_dir_name (str): Name of the download summary directory
        
    Returns:
        dict: Dictionary with paths to all created directories
    """
    # Create base directory if it doesn't exist
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # Create chat-specific directory
    chat_dir = os.path.join(base_dir, chat_id)
    if not os.path.exists(chat_dir):
        os.makedirs(chat_dir)
    
    # Create subdirectories
    search_results_dir = os.path.join(chat_dir, search_dir_name)
    smart_search_results_dir = os.path.join(chat_dir, smart_search_dir_name)
    downloaded_pdfs_dir = os.path.join(chat_dir, download_dir_name)
    download_summary_dir = os.path.join(chat_dir, summary_dir_name)
    
    for directory in [search_results_dir, smart_search_results_dir, downloaded_pdfs_dir, download_summary_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    return {
        "base_dir": base_dir,
        "chat_dir": chat_dir,
        "search_results_dir": search_results_dir,
        "smart_search_results_dir": smart_search_results_dir,
        "downloaded_pdfs_dir": downloaded_pdfs_dir,
        "download_summary_dir": download_summary_dir
    }

def extract_evaluation_data(llm_response: str) -> Dict[str, Any]:
    """
    Extract evaluation data from LLM response using regex.
    
    Args:
        llm_response (str): Response from the LLM
        
    Returns:
        Dict[str, Any]: Extracted evaluation data
    """
    # Extract local_id
    local_id_match = re.search(r'<local_id>(.*?)</local_id>', llm_response)
    local_id = local_id_match.group(1) if local_id_match else ""
    
    # Extract score
    score_match = re.search(r'<score>(\d+)</score>', llm_response)
    score = int(score_match.group(1)) if score_match else 0
    
    # Extract download decision
    download_match = re.search(r'<download>(yes|no)</download>', llm_response.lower())
    download = download_match.group(1) == 'yes' if download_match else False
    
    # Extract reasoning
    reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', llm_response, re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

    apareference_match = re.search(r'<apareference>(.*?)</apareference>', llm_response, re.DOTALL)
    apareference = apareference_match.group(1).strip() if apareference_match else "None"

    return {
        "local_id": local_id,
        "score": score,
        "download": download,
        "reasoning": reasoning,
        "apareference": apareference,
        "citation": apareference  # Add citation field
    }

def chunk_papers(papers: List[Dict[str, Any]], batch_size: int = BATCH_SIZE) -> List[List[Dict[str, Any]]]:
    """
    Split papers into batches for processing.
    
    Args:
        papers (List[Dict[str, Any]]): List of paper data
        batch_size (int): Size of each batch
        
    Returns:
        List[List[Dict[str, Any]]]: List of batches
    """
    return [papers[i:i + batch_size] for i in range(0, len(papers), batch_size)]

async def evaluate_paper_batch(llm, papers: List[Dict[str, Any]], research_query: str) -> List[Dict[str, Any]]:
    """
    Evaluate a batch of papers using the LLM.
    
    Args:
        llm: LangChain LLM instance
        papers (List[Dict[str, Any]]): Batch of papers (up to 10)
        research_query (str): Original research query
        
    Returns:
        List[Dict[str, Any]]: Evaluation results for the batch
    """
    # Convert papers to JSON string
    papers_json = json.dumps(papers, indent=2)
    print('batch of papers (JSON): ', papers_json)
    
    # Create prompt for LLM
    prompt = f"""
You are a research assistant evaluating papers for relevance to a research query.

Research Query: "{research_query}"

I will provide you with {len(papers)} papers in JSON format. For each paper, evaluate its relevance to the research query.
Also provide an APA reference using APA style for references for my research paper to the best of the given information.

PAPERS JSON:
{papers_json}

For EACH paper, provide your evaluation in the following format:

<paper>
<local_id>PAPER_LOCAL_ID</local_id>
<score>SCORE_NUMBER</score>
<download>yes/no</download>
<reasoning>Your reasoning here</reasoning>
<apareference>APA reference to the paper here</apareference>
</paper>

Score each paper from 0-100 where:
- 0-20: Not relevant at all
- 21-40: Slightly relevant but not useful
- 41-60: Moderately relevant
- 61-80: Highly relevant
- 81-100: Extremely relevant and essential

Also decide whether each paper should be downloaded for further review (yes/no).
Make sure to include the exact local_id for each paper in your response.
You MUST evaluate ALL {len(papers)} papers and include the local_id exactly as provided.
"""
    
    # Call LLM
    messages = [HumanMessage(content=prompt)]
    
    # Add retry logic with exponential backoff
    max_retries = 5
    base_delay = 2  # Start with 2 second delay for larger batches
    
    for retry in range(max_retries):
        try:
            response = await llm.ainvoke(messages)
            response_text = response.content
            break  # If successful, break out of the retry loop
        except Exception as e:
            # Check if it's a rate limit error
            if "429" in str(e) or "Resource has been exhausted" in str(e):
                # Calculate delay with exponential backoff
                delay = base_delay * (2 ** retry)
                print(f"Rate limit hit. Retrying in {delay} seconds... (Attempt {retry+1}/{max_retries})")
                await asyncio.sleep(delay)
                if retry == max_retries - 1:  # If this was the last retry
                    print(f"Failed after {max_retries} retries. Error: {str(e)}")
                    raise
            else:
                # If it's not a rate limit error, re-raise immediately
                print(f"Error calling LLM: {str(e)}")
                raise
    
    # Extract evaluations for each paper
    paper_evaluations = []
    paper_matches = re.finditer(r'<paper>(.*?)</paper>', response_text, re.DOTALL)
    
    for match in paper_matches:
        paper_text = match.group(1)
        evaluation = extract_evaluation_data(paper_text)
        paper_evaluations.append(evaluation)
    
    # If we didn't get evaluations for all papers, log a warning
    if len(paper_evaluations) < len(papers):
        print(f"Warning: Only received {len(paper_evaluations)} evaluations for {len(papers)} papers")
        # Try to match papers with evaluations by local_id
        for paper in papers:
            local_id = paper.get('local_id', '')
            if not any(eval.get('local_id') == local_id for eval in paper_evaluations):
                # Add a default evaluation
                paper_evaluations.append({
                    "local_id": local_id,
                    "score": 50,  # Default middle score
                    "download": False,
                    "reasoning": "Evaluation failed or missing from LLM response",
                    "apareference": "NA"
                })
    
    return paper_evaluations

async def smart_evaluate_papers(
    papers: List[Dict[str, Any]],
    research_query: str,
    output_file: str = None,
    batch_size: int = BATCH_SIZE,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Evaluate papers using LLM and save results.
    
    Args:
        papers (List[Dict[str, Any]]): List of papers to evaluate
        research_query (str): Original research query
        output_file (str, optional): Path to save evaluation results
        batch_size (int): Number of papers to process in each batch (default 10)
        verbose (bool): Whether to print progress messages
        
    Returns:
        Dict[str, Any]: Summary of evaluation results
    """
    if verbose:
        print(f"Starting smart evaluation of {len(papers)} papers")
        print(f"Research query: {research_query}")
        print(f"Processing in batches of {batch_size} papers")
    
    # Initialize LLM
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()]) if verbose else None
    
    llm = ChatGoogleGenerativeAI(
        # model="gemini-2.0-flash",
        model="gemini-1.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
        callback_manager=callback_manager if verbose else None,
        streaming=False
    )
    # print('papers: ', papers)
    # Split papers into batches
    paper_batches = chunk_papers(papers, batch_size)
    
    if verbose:
        total_papers = len(papers)
        total_batches = len(paper_batches)
        last_batch_size = len(papers) % batch_size if len(papers) % batch_size != 0 else batch_size
        
        print(f"Total papers to evaluate: {total_papers}")
        print(f"Processing in {total_batches} batches of up to {batch_size} papers each")
        if total_papers % batch_size != 0:
            print(f"Last batch will contain {last_batch_size} papers")
    
    # Process batches
    evaluated_papers = []
    
    for i, batch in enumerate(paper_batches):
        if verbose:
            print(f"\nProcessing batch {i+1}/{len(paper_batches)} ({len(batch)} papers)")
        
        # Add a delay of 2 seconds between API calls to avoid rate limits
        # Larger delay for larger batches to ensure we don't hit rate limits
        if i > 0:  # Don't delay the first batch
            delay_seconds = 2  # Increased delay for larger batches
            await asyncio.sleep(delay_seconds)
            if verbose:
                print(f"Waiting {delay_seconds} seconds before processing next batch to avoid rate limits...")
        
        # Evaluate the batch
        batch_evaluations = await evaluate_paper_batch(llm, batch, research_query)
        
        # Match evaluations with papers by local_id and update the original papers
        for paper in batch:
            paper_copy = paper.copy()  # Create a copy to avoid modifying the original
            local_id = paper_copy.get('local_id', '')
            
            # Find matching evaluation
            matching_eval = next((eval for eval in batch_evaluations if eval.get('local_id') == local_id), None)
            
            if matching_eval:
                # Add evaluation to paper
                paper_copy["evaluation"] = {
                    "score": matching_eval["score"],
                    "download": matching_eval["download"],
                    "reasoning": matching_eval["reasoning"],
                    "citation": matching_eval.get("citation", "None")  # Add citation field
                }
            else:
                # Add default evaluation if no match found
                paper_copy["evaluation"] = {
                    "score": 50,  # Default middle score
                    "download": False,
                    "reasoning": "No evaluation found for this paper",
                    "citation": "None"  # Add default citation
                }
            
            evaluated_papers.append(paper_copy)
        
        if verbose:
            print(f"Completed batch {i+1}/{len(paper_batches)}")
            # Print a summary of this batch
            download_count = sum(1 for p in batch if next((e for e in batch_evaluations if e.get('local_id') == p.get('local_id')), {}).get('download', False))
            print(f"  Papers recommended for download in this batch: {download_count}/{len(batch)}")
    
    # Prepare summary
    papers_to_download = [p for p in evaluated_papers if p.get("evaluation", {}).get("download", False)]
    
    summary = {
        "total_papers": len(papers),
        "papers_evaluated": len(evaluated_papers),
        "papers_to_download": len(papers_to_download),
        "average_score": sum(p.get("evaluation", {}).get("score", 0) for p in evaluated_papers) / len(evaluated_papers) if evaluated_papers else 0,
        "papers": evaluated_papers
    }
    
    # Save results if output file is provided
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        if verbose:
            print(f"\nEvaluation results saved to: {output_file}")
    
    if verbose:
        print("\nEvaluation summary:")
        print(f"Total papers: {summary['total_papers']}")
        print(f"Papers to download: {summary['papers_to_download']}")
        print(f"Average score: {summary['average_score']:.2f}")
    
    return summary

async def process_query(
    # Query parameters
    query, 
    from_date=None, 
    until_date=None,
    limit=10, 
    convert_query=True,
    save_raw_responses=True,
    
    # Download parameters
    max_papers=5, 
    skip_existing=True,
    max_concurrent=3,
    
    # Folder structure parameters
    chat_id=None,
    base_dir="file_downloads",
    search_dir_name="search_results",
    smart_search_dir_name="smart_search_results",
    download_dir_name="downloaded_pdfs",
    summary_dir_name="download_summary",
    
    # File naming parameters
    search_results_filename="search_results.json",
    smart_results_filename="smart_results.json",
    download_summary_filename="download_summary.json",
    
    # Behavior parameters
    verbose=True,
    return_papers=True,
    
    # Evaluation parameters
    evaluate_papers=True,
    download_only_evaluated=True,
    batch_size=BATCH_SIZE
):
    """
    Process a query: search for papers, evaluate them with LLM, and download selected papers
    
    Args:
        # Query parameters
        query (str): The search query
        from_date (str): Start date in YYYY-MM-DD format
        until_date (str): End date in YYYY-MM-DD format
        limit (int): Maximum number of papers to retrieve
        convert_query (bool): Whether to convert natural language to keywords
        save_raw_responses (bool): Whether to save raw API responses
        
        # Download parameters
        max_papers (int): Maximum number of papers to download
        skip_existing (bool): Whether to skip existing files
        max_concurrent (int): Maximum number of concurrent downloads
        
        # Folder structure parameters
        chat_id (str): Custom chat ID (if None, one will be generated)
        base_dir (str): Base directory for file_downloads
        search_dir_name (str): Name of the search results directory
        smart_search_dir_name (str): Name of the smart search results directory
        download_dir_name (str): Name of the downloaded PDFs directory
        summary_dir_name (str): Name of the download summary directory
        
        # File naming parameters
        search_results_filename (str): Filename for search results
        smart_results_filename (str): Filename for smart evaluation results
        download_summary_filename (str): Filename for download summary
        
        # Behavior parameters
        verbose (bool): Whether to print progress messages
        return_papers (bool): Whether to return the papers in the result
        
        # Evaluation parameters
        evaluate_papers (bool): Whether to evaluate papers with LLM
        download_only_evaluated (bool): Whether to download only papers that pass evaluation
        batch_size (int): Number of papers to evaluate in each batch
        
    Returns:
        dict: Results including chat_id, paths, and optionally papers and download results
    """
    # 1. Generate a unique chat_id for this query if not provided
    if not chat_id:
        chat_id = generate_chat_id()
    
    if verbose:
        print(f"Generated chat_id: {chat_id}")
    
    # 2. Create folder structure
    folders = create_folder_structure(
        chat_id, 
        base_dir=base_dir,
        search_dir_name=search_dir_name,
        smart_search_dir_name=smart_search_dir_name,
        download_dir_name=download_dir_name,
        summary_dir_name=summary_dir_name
    )
    
    if verbose:
        print(f"Created folder structure in: {folders['chat_dir']}")
        print(f"Step 1: Searching for papers on: {query}")
        if from_date:
            print(f"From date: {from_date}")
        if until_date:
            print(f"Until date: {until_date}")
        print(f"Limit: {limit}")
        print("Please wait...")
    
    # 3. Generate search results filename
    search_results_path = os.path.join(folders["search_results_dir"], search_results_filename)
    
    # 4. Perform search
    papers = await search_papers(
        query=query,
        limit=limit,
        from_date=from_date,
        until_date=until_date,
        output_file=search_results_path,
        convert_query=convert_query,
        save_raw_responses=save_raw_responses
    )
    
    if verbose:
        print(f"\nFound {len(papers)} papers")
        print(f"Search results saved to: {search_results_path}")
    
    # 5. Evaluate papers if requested
    smart_results_path = None
    evaluation_results = None
    papers_to_download = papers  # Default: download all papers
    
    if evaluate_papers and papers:
        if verbose:
            print(f"\nStep 2: Evaluating papers with LLM")
            print("Please wait...")
            print("Note: A 2-second delay has been added between API calls to avoid rate limits.")
        
        # Generate smart results filename
        smart_results_path = os.path.join(folders["smart_search_results_dir"], smart_results_filename)
        
        # Perform evaluation
        evaluation_results = await smart_evaluate_papers(
            papers=papers,
            research_query=query,
            output_file=smart_results_path,
            batch_size=batch_size,
            verbose=verbose
        )
        
        if verbose:
            print(f"\nEvaluation completed")
            print(f"Smart results saved to: {smart_results_path}")
        
        # Filter papers to download if requested
        if download_only_evaluated:
            papers_to_download = [p for p in evaluation_results["papers"] if p["evaluation"]["download"]]
            
            # Limit to max_papers if specified
            if max_papers and len(papers_to_download) > max_papers:
                # Sort by score (highest first)
                papers_to_download = sorted(papers_to_download, 
                                          key=lambda p: p["evaluation"]["score"],
                                          reverse=True)
                papers_to_download = papers_to_download[:max_papers]
    
    # 6. Download papers
    if verbose:
        print(f"\nStep {'3' if evaluate_papers else '2'}: Downloading papers")
        print(f"Papers to download: {len(papers_to_download)}")
        print("Please wait...")
    
    # Generate download summary filename
    download_summary_path = os.path.join(folders["download_summary_dir"], download_summary_filename)
    
    # Save filtered papers to a temporary file for download if needed
    download_input_file = search_results_path
    if evaluate_papers and download_only_evaluated:
        filtered_papers_path = os.path.join(folders["smart_search_results_dir"], "filtered_papers.json")
        with open(filtered_papers_path, 'w', encoding='utf-8') as f:
            json.dump(papers_to_download, f, indent=2)
        download_input_file = filtered_papers_path
    
    # Perform download
    download_results = await download_papers(
        input_file=download_input_file,
        output_dir=folders["downloaded_pdfs_dir"],
        max_papers=max_papers if not (evaluate_papers and download_only_evaluated) else None,  # Already limited above
        skip_existing=skip_existing,
        max_concurrent=max_concurrent,
        save_summary_to=download_summary_path
    )
    
    # 7. Print final summary if verbose
    if verbose:
        print("\nProcess completed!")
        print(f"Chat ID: {chat_id}")
        print(f"Search results saved to: {search_results_path}")
        if evaluate_papers:
            print(f"Smart evaluation results saved to: {smart_results_path}")
        print(f"Downloaded papers saved to: {folders['downloaded_pdfs_dir']}")
        print(f"Download summary saved to: {download_summary_path}")
    
    # 8. Verify downloaded files and update download results
    downloaded_files = []
    if os.path.exists(folders["downloaded_pdfs_dir"]):
        downloaded_files = [f for f in os.listdir(folders["downloaded_pdfs_dir"]) if f.lower().endswith('.pdf')]
    
    # Load the download summary if it exists
    download_summary = {}
    if os.path.exists(download_summary_path):
        try:
            with open(download_summary_path, 'r', encoding='utf-8') as f:
                download_summary = json.load(f)
        except Exception as e:
            print(f"Error loading download summary: {str(e)}")
    
    # 9. Prepare result
    result = {
        "chat_id": chat_id,
        "folders": folders,
        "search_results": papers,
        "search_results_path": search_results_path,
        "download_summary_path": download_summary_path,
        "download_results": download_results,
        "download_summary": download_summary,
        "actual_downloaded_files": downloaded_files
    }
    
    # Add evaluation results if available
    if evaluate_papers and evaluation_results:
        result["evaluation_results"] = evaluation_results
        result["smart_results_path"] = smart_results_path
    
    # Return the result
    if return_papers:
        return result
    else:
        # Remove large data structures if not needed
        result_copy = result.copy()
        if "search_results" in result_copy:
            del result_copy["search_results"]
        if "evaluation_results" in result_copy:
            del result_copy["evaluation_results"]
        if "download_summary" in result_copy:
            del result_copy["download_summary"]
        return result_copy

async def main():
    """
    Example usage of the fetch and download flow
    """
    # Example query
    query = "Recent advances in transformer models for natural language processing"
    
    # Process the query with smart evaluation
    result = await process_query(
        query=query,
        limit=20,
        max_papers=5,
        evaluate_papers=True,
        download_only_evaluated=True,
        batch_size=10,  # Using the default batch size
        verbose=True
    )
    
    print("\nProcess completed successfully!")
    print(f"Chat ID: {result['chat_id']}")
    print(f"Search results: {result['search_results_path']}")
    print(f"Smart evaluation results: {result['smart_results_path']}")
    print(f"Downloaded papers: {result['folders']['downloaded_pdfs_dir']}")

if __name__ == "__main__":
    asyncio.run(main())
