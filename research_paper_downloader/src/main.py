"""
Main entry point for the research paper downloader.
"""

import os
import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from .config import (
    CROSSREF_EMAIL, PUBMED_EMAIL, PUBMED_TOOL,
    SEMANTIC_SCHOLAR_API_KEY, DEFAULT_HEADERS, USE_PROXIES,
    DOWNLOAD_DIR, SEARCH_SOURCES, SERPER_API_KEY
)
from .utils.proxy_manager import ProxyManager
from .utils.doi_validator import normalize_doi

# Import searchers
from .searchers.crossref import CrossrefSearcher
from .searchers.pubmed import PubMedSearcher
from .searchers.semantic_scholar import SemanticScholarSearcher
from .searchers.google_scholar import GoogleScholarSearcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_paper_id(paper: Dict[str, Any]) -> str:
    """
    Generate a unique ID for a paper based on its metadata.
    
    Returns:
        str: Unique ID for the paper
    """
    # Generate a random UUID
    return f"paper_{uuid.uuid4().hex[:12]}"

class ResearchPaperSearcher:
    """
    Simplified class for searching research papers from various sources.
    """
    def __init__(self, use_proxies: bool = USE_PROXIES):
        """Initialize the research paper searcher."""
        self.proxy_manager = ProxyManager() if use_proxies else None
        
        # Initialize searchers
        self.searchers = {
            "crossref": CrossrefSearcher(email=CROSSREF_EMAIL),
            "pubmed": PubMedSearcher(tool=PUBMED_TOOL, email=PUBMED_EMAIL),
            "semantic_scholar": SemanticScholarSearcher(api_key=SEMANTIC_SCHOLAR_API_KEY),
            "google_scholar": GoogleScholarSearcher(api_key=SERPER_API_KEY)
        }

    async def search_papers(
        self,
        query: str,
        limit: int = 100,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        save_raw_responses: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for papers using multiple sources."""
        results = []
        seen_dois = set()
        seen_titles = set()
        errors = []
        
        # Create a unique folder for raw responses if enabled
        raw_dir = None
        if save_raw_responses:
            # Create base raw_responses directory if it doesn't exist
            raw_responses_base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                            "raw_responses")
            os.makedirs(raw_responses_base, exist_ok=True)
            
            # Create timestamped subfolder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_dir = os.path.join(raw_responses_base, f"search_{timestamp}")
            os.makedirs(raw_dir, exist_ok=True)
            logger.info(f"Saving raw responses to: {raw_dir}")
        
        for source in SEARCH_SOURCES:
            if source not in self.searchers:
                continue
                
            try:
                logger.debug(f"Searching {source} for: {query}")
                
                # Get raw response from searcher
                source_results, raw_response = await self.searchers[source].search_with_raw(
                    query=query,
                    limit=limit,
                    from_date=from_date,
                    until_date=until_date
                )
                
                # Save raw response if enabled
                if save_raw_responses and raw_response and raw_dir:
                    raw_file = os.path.join(raw_dir, f"{source}_raw.json")
                    with open(raw_file, 'w', encoding='utf-8') as f:
                        json.dump(raw_response, f, indent=2, ensure_ascii=False)
                    logger.info(f"Saved raw {source} response to: {raw_file}")
                
                # Count valid results
                valid_count = 0
                
                logger.debug(f"Received {len(source_results)} results from {source}")
                
                # Deduplicate by DOI
                for paper in source_results:
                    # Add source information to the paper
                    paper['fetched_source'] = source
                    
                    # Add a unique ID to the paper
                    paper['local_id'] = generate_paper_id(paper)
                    
                    doi = paper.get('doi')
                    title = paper.get('title')
                    
                    # Handle papers without DOI (common in Google Scholar)
                    if not doi and source == "google_scholar" and title:
                        if title not in seen_titles:
                            seen_titles.add(title)
                            results.append(paper)
                            valid_count += 1
                    # Handle papers with DOI
                    elif doi and doi not in seen_dois:
                        seen_dois.add(doi)
                        results.append(paper)
                        valid_count += 1
                        
                logger.debug(f"Found {valid_count} new papers from {source}")
                        
            except Exception as e:
                error_msg = f"Error searching {source}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                
        if not results and errors:
            logger.error("All search sources failed")
            for error in errors:
                logger.error(error)
                
        return results

# Example usage
async def example():
    searcher = ResearchPaperSearcher(use_proxies=False)
    
    # Search for papers
    papers = await searcher.search_papers(
        query="machine learning",
        limit=5,
        from_date="2023-01-01"
    )
    
    # Print results
    print(f"\nFound {len(papers)} papers:")
    for paper in papers:
        print(f"- {paper.get('title', 'No title')}")
        print(f"  DOI: {paper.get('doi', 'No DOI')}")
        print(f"  Source: {paper.get('fetched_source', 'Unknown')}")
        print()

if __name__ == "__main__":
    asyncio.run(example()) 