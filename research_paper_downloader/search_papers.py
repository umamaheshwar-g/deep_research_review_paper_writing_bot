import asyncio
import json
import re
import os
from datetime import datetime
from typing import Dict, Any, List
from .src.main import ResearchPaperSearcher

def convert_to_keyword_query(query: str) -> str:
    """
    Convert a natural language query to a keyword-based query.
    
    Args:
        query (str): Natural language query
        
    Returns:
        str: Keyword-based query
    """
    # Remove punctuation and convert to lowercase
    query = re.sub(r'[^\w\s]', ' ', query.lower())
    
    # Define common stop words to remove
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
        'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than', 'such',
        'when', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        'can', 'will', 'should', 'now', 'to', 'of', 'for', 'with', 'about', 'against',
        'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'having', 'do', 'does', 'did', 'doing', 'would', 'should', 'could', 'ought',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'their', 'his', 'her', 'its',
        'ours', 'yours', 'theirs', 'me', 'him', 'us', 'them'
    }
    
    # Split into words and filter out stop words
    words = query.split()
    keywords = [word for word in words if word not in stop_words and len(word) > 1]
    
    # Join keywords with AND for better search results
    return ' '.join(keywords)

async def search_papers(
    query: str,
    limit: int = 100,
    from_date: str = None,
    until_date: str = None,
    output_file: str = None,
    save_raw_responses: bool = True,
    convert_query: bool = True
) -> List[Dict[str, Any]]:
    """
    Search for papers using multiple sources.
    
    Args:
        query (str): Search query
        limit (int, optional): Maximum number of results to return. Defaults to 100.
        from_date (str, optional): Start date in YYYY-MM-DD format. Defaults to None.
        until_date (str, optional): End date in YYYY-MM-DD format. Defaults to None.
        output_file (str, optional): Path to save results as JSON. Defaults to None.
        save_raw_responses (bool, optional): Whether to save raw API responses. Defaults to True.
        convert_query (bool, optional): Whether to convert natural language to keywords. Defaults to True.
        
    Returns:
        List[Dict[str, Any]]: List of paper metadata
    """
    # Convert natural language query to keywords if requested
    if convert_query:
        original_query = query
        query = convert_to_keyword_query(query)
        print(f"Converted query: '{original_query}' -> '{query}'")
    
    # Initialize downloader
    searcher = ResearchPaperSearcher(use_proxies=False)
    
    # Search for papers
    papers = await searcher.search_papers(
        query=query,
        limit=limit,
        from_date=from_date,
        until_date=until_date,
        save_raw_responses=save_raw_responses
    )
    
    # Save results to file if requested
    if output_file:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(papers)} papers to {output_file}")
    
    return papers

async def main():
    # Example usage with a more PubMed-friendly query
    query = " What are the current technological advancements and innovations in Hyperloop transportation"
    from_date = "2023-01-01"  # Optional: papers from 2023 onwards
    limit = 10  # Number of papers to retrieve
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"search_results_{timestamp}.json"
    
    print(f"Searching for: {query}")
    print(f"From date: {from_date}")
    print(f"Limit: {limit}")
    print("Please wait...")
    
    papers = await search_papers(
        query=query,
        limit=limit,
        from_date=from_date,
        output_file=output_file,
        convert_query=True
    )
    
    # Print summary
    print(f"\nFound {len(papers)} papers")
    
    # Print papers as example
    print("\nResults:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.get('title', 'No title')}")
        if paper.get('doi'):
            print(f"   DOI: {paper['doi']}")
        if paper.get('authors'):
            print(f"   Authors: {', '.join(paper['authors'])}")
        if paper.get('fetched_source'):
            print(f"   Source: {paper['fetched_source']}")

# Only run the main function if this script is executed directly
if __name__ == "__main__":
    asyncio.run(main())
