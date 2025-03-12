"""
Google Scholar API interface for searching research papers using Serper.dev.
"""

import aiohttp
import json
from typing import List, Dict, Any, Optional
import logging
from ..config import DEFAULT_HEADERS, SERPER_API_KEY
from ..utils.doi_validator import normalize_doi, extract_doi_from_url
import re

logger = logging.getLogger(__name__)

class GoogleScholarSearcher:
    BASE_URL = "https://google.serper.dev/scholar"
    
    def __init__(self, api_key: str = SERPER_API_KEY):
        """
        Initialize the Google Scholar searcher.
        
        Args:
            api_key (str): API key for Serper.dev.
        """
        self.headers = DEFAULT_HEADERS.copy()
        self.headers['X-API-KEY'] = api_key
        self.headers['Content-Type'] = 'application/json'

    async def search(
        self,
        query: str,
        limit: int = 10,
        paper_types: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Google Scholar via Serper API.
        
        Args:
            query (str): Search query.
            limit (int): Maximum number of results to return.
            paper_types (Optional[List[str]]): List of paper types to include (not used).
            from_date (Optional[str]): Start date in format YYYY-MM-DD (not directly supported).
            until_date (Optional[str]): End date in format YYYY-MM-DD (not directly supported).
            **kwargs: Additional arguments to pass to the API.
            
        Returns:
            List[Dict[str, Any]]: List of paper metadata.
        """
        results, _ = await self.search_with_raw(
            query=query,
            limit=limit,
            paper_types=paper_types,
            from_date=from_date,
            until_date=until_date,
            **kwargs
        )
        return results
        
    async def search_with_raw(
        self,
        query: str,
        limit: int = 10,
        paper_types: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        **kwargs
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Search for papers and return both processed results and raw response.
        
        Args:
            query (str): Search query.
            limit (int): Maximum number of results to return.
            paper_types (Optional[List[str]]): List of paper types to include (not used).
            from_date (Optional[str]): Start date in format YYYY-MM-DD (not directly supported).
            until_date (Optional[str]): End date in format YYYY-MM-DD (not directly supported).
            **kwargs: Additional arguments to pass to the API.
            
        Returns:
            tuple: (processed_results, raw_response)
        """
        # Add date range to query if specified
        original_query = query
        if from_date and until_date:
            query = f"{query} after:{from_date[:4]} before:{until_date[:4]}"
        elif from_date:
            query = f"{query} after:{from_date[:4]}"
        elif until_date:
            query = f"{query} before:{until_date[:4]}"

        logger.info(f"Google Scholar search query: '{query}' (original: '{original_query}')")
        
        # Prepare request payload
        payload = json.dumps({
            "q": query,
            "autocorrect": False
        })

        logger.info(f"Sending request to {self.BASE_URL}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.BASE_URL,
                    headers=self.headers,
                    data=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from Serper API: Status {response.status}, Response: {error_text}")
                        return [], None
                        
                    data = await response.json()
                    logger.info(f"Google Scholar API response status: {response.status}")
                    logger.info(f"Response contains keys: {list(data.keys())}")
                    
                    # Parse results
                    papers = []
                    organic_results = data.get('organic', [])
                    logger.info(f"Found {len(organic_results)} organic results")
                    
                    for item in organic_results[:limit]:
                        paper = self._parse_paper(item)
                        if paper:
                            papers.append(paper)

                    logger.info(f"Successfully parsed {len(papers)} papers out of {len(organic_results[:limit])} results")
                    return papers, data
                    
            except Exception as e:
                logger.error(f"Error searching Google Scholar: {str(e)}")
                return [], None

    def _parse_paper(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse paper metadata from Google Scholar API response.
        
        Args:
            item (Dict[str, Any]): Paper metadata from Google Scholar API.
            
        Returns:
            Optional[Dict[str, Any]]: Parsed paper metadata or None if invalid.
        """
        # Try to extract DOI from link or PDF URL
        doi = None
        if 'link' in item:
            doi = extract_doi_from_url(item['link'])
        
        if not doi and 'pdfUrl' in item:
            doi = extract_doi_from_url(item['pdfUrl'])
            
        # Skip if no DOI could be extracted
        if not doi:
            # For Google Scholar, we'll keep papers even without DOI
            # as they might still be valuable
            pass
        else:
            doi = normalize_doi(doi)

        # Extract publication year
        year = item.get('year')
        if isinstance(year, str) and year.isdigit():
            published = year
        else:
            published = None

        # Extract authors and journal from publication info
        authors = []
        journal = None
        volume = None
        issue = None
        pages = None
        
        pub_info = item.get('publicationInfo', '')
        if pub_info:
            # Try to extract authors (typically before the dash)
            if ' - ' in pub_info:
                author_part = pub_info.split(' - ')[0]
                potential_authors = author_part.split(', ')
                for author in potential_authors:
                    if '…' not in author:  # Skip truncated author lists
                        authors.append(author.strip())
                
                # Try to extract journal (typically after the dash)
                journal_part = pub_info.split(' - ')[1] if len(pub_info.split(' - ')) > 1 else None
                if journal_part:
                    # Try to extract journal name and volume/issue/pages
                    journal_info = journal_part.split(' - ')[0].strip() if ' - ' in journal_part else journal_part.strip()
                    
                    # Common patterns: "Journal Name, vol(issue), pp-pp" or "Journal Name, vol, pp-pp"
                    journal = journal_info
                    
                    # Try to extract volume, issue, and pages using regex
                    vol_issue_pattern = r'(?:,\s*|^)(\d+)(?:\((\d+)\))?(?:,\s*(?:pp\.\s*)?(\d+[-–]\d+))?'
                    vol_issue_match = re.search(vol_issue_pattern, journal_info)
                    
                    if vol_issue_match:
                        # Remove the volume/issue/pages part from journal name
                        journal = re.sub(vol_issue_pattern, '', journal_info).strip().rstrip(',')
                        
                        # Extract volume, issue, and pages
                        volume = vol_issue_match.group(1)
                        issue = vol_issue_match.group(2)
                        pages = vol_issue_match.group(3)

        # Build paper metadata
        paper = {
            'doi': doi,
            'title': item.get('title'),
            'type': 'journal-article',  # Default type
            'published': published,
            'publisher': None,  # Not provided by API
            'journal': journal,
            'authors': authors,
            'abstract': item.get('snippet'),
            'url': item.get('link'),
            'citations_count': item.get('citedBy'),
            'pdf_url': item.get('pdfUrl'),
            'google_scholar_id': item.get('id'),
            
            # Add additional fields
            'volume': volume,
            'issue': issue,
            'pages': pages,
            'publication_date': None,  # Google Scholar doesn't provide full dates
            'keywords': [],  # Google Scholar doesn't provide keywords
            'source_specific': {
                'google_scholar': {
                    'publication_info': pub_info,
                    'raw_id': item.get('id')
                }
            }
        }
        
        # Store any additional useful information in source_specific
        if 'resources' in item:
            paper['source_specific']['google_scholar']['resources'] = item['resources']
            
        if 'authors' in item:
            paper['source_specific']['google_scholar']['raw_authors'] = item['authors']

        return paper

    async def get_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper metadata by Google Scholar ID.
        
        Note: Serper API doesn't support direct lookup by ID, so we can't implement this.
        
        Args:
            paper_id (str): Google Scholar paper ID.
            
        Returns:
            Optional[Dict[str, Any]]: Paper metadata or None if not found.
        """
        logger.warning("Direct lookup by Google Scholar ID is not supported by the Serper API")
        return None 