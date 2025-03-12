"""
Crossref API interface for searching research papers.
"""

import aiohttp
from typing import List, Dict, Any, Optional
from ..config import CROSSREF_EMAIL, DEFAULT_SEARCH_LIMIT, SUPPORTED_PAPER_TYPES, DEFAULT_HEADERS
import logging

logger = logging.getLogger(__name__)

class CrossrefSearcher:
    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, email: str = CROSSREF_EMAIL):
        """
        Initialize the Crossref searcher.
        
        Args:
            email (str): Email to use for Crossref API.
        """
        self.email = email
        self.headers = DEFAULT_HEADERS.copy()
        self.headers['User-Agent'] += f" (mailto:{email})"

    async def search(
        self,
        query: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        paper_types: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Crossref API.
        
        Args:
            query (str): Search query.
            limit (int): Maximum number of results to return.
            paper_types (Optional[List[str]]): List of paper types to include.
            from_date (Optional[str]): Start date in format YYYY-MM-DD.
            until_date (Optional[str]): End date in format YYYY-MM-DD.
            **kwargs: Additional arguments to pass to Crossref API.
            
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
        limit: int = DEFAULT_SEARCH_LIMIT,
        paper_types: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        **kwargs
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Search for papers and return both processed results and raw response.
        
        Args:
            Same as search method.
            
        Returns:
            tuple: (processed_results, raw_response)
        """
        # Set up filter parameters
        filters = {}
        
        if paper_types:
            valid_types = [t for t in paper_types if t in SUPPORTED_PAPER_TYPES]
            if valid_types:
                filters['type'] = valid_types
        
        if from_date:
            filters['from-pub-date'] = from_date
            
        if until_date:
            filters['until-pub-date'] = until_date

        # Build query parameters
        params = {
            'query': query,
            'rows': limit,
            'mailto': self.email
        }
        
        if filters:
            params['filter'] = ','.join(f"{k}:{v}" for k, v in filters.items())

        logger.info(f"Searching Crossref with query: {query}, params: {params}")
        
        # Perform the search
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self.BASE_URL,
                    params=params,
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Error from Crossref API: {response.status}")
                        return [], None
                        
                    data = await response.json()
                    logger.info(f"Received response from Crossref API with status: {response.status}")
                    
                    # Extract items from response
                    items = data.get('message', {}).get('items', [])
                    logger.info(f"Found {len(items)} items in Crossref response")
                    
                    # Parse results
                    results = []
                    for item in items:
                        paper = self._parse_paper(item)
                        if paper:
                            results.append(paper)
                    
                    logger.info(f"Successfully parsed {len(results)} papers from Crossref")
                    return results, data
                    
            except Exception as e:
                logger.error(f"Error searching Crossref: {str(e)}")
                return [], None

    def _parse_paper(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse paper metadata from Crossref API response.
        
        Args:
            item (Dict[str, Any]): Paper metadata from Crossref API.
            
        Returns:
            Optional[Dict[str, Any]]: Parsed paper metadata or None if invalid.
        """
        # Skip if no DOI
        if 'DOI' not in item:
            return None

        # Extract basic metadata
        paper = {
            'doi': item['DOI'],
            'title': item.get('title', [None])[0],
            'type': item.get('type'),
            'published': item.get('published-print', {}).get('date-parts', [[None]])[0][0],
            'publisher': item.get('publisher'),
            'journal': item.get('container-title', [None])[0],
            'authors': [],
            'abstract': None,
            'url': item.get('URL'),
            'references_count': item.get('references-count'),
            'citations_count': item.get('is-referenced-by-count'),
            
            # Add additional fields
            'volume': None,
            'issue': None,
            'pages': None,
            'publication_date': None,
            'license': None,
            'keywords': [],
            'source_specific': {
                'crossref': {}
            }
        }

        # Extract authors
        if 'author' in item:
            for author in item['author']:
                name_parts = []
                if 'given' in author:
                    name_parts.append(author['given'])
                if 'family' in author:
                    name_parts.append(author['family'])
                if name_parts:
                    paper['authors'].append(' '.join(name_parts))

        # Extract abstract if available
        if 'abstract' in item:
            paper['abstract'] = item['abstract']
            
        # Extract volume, issue, and pages
        paper['volume'] = item.get('volume')
        paper['issue'] = item.get('issue')
        paper['pages'] = item.get('page')
        
        # Extract publication date (more detailed than just year)
        if 'published-print' in item and 'date-parts' in item['published-print']:
            date_parts = item['published-print']['date-parts'][0]
            if len(date_parts) >= 3:  # Year, month, day
                paper['publication_date'] = f"{date_parts[0]}-{date_parts[1]:02d}-{date_parts[2]:02d}"
            elif len(date_parts) >= 2:  # Year, month
                paper['publication_date'] = f"{date_parts[0]}-{date_parts[1]:02d}-01"
            elif len(date_parts) >= 1:  # Year only
                paper['publication_date'] = f"{date_parts[0]}-01-01"
        
        # Extract license information
        if 'license' in item and isinstance(item['license'], list) and len(item['license']) > 0:
            license_info = item['license'][0]
            paper['license'] = license_info.get('URL')
            # Store more detailed license info in source_specific
            paper['source_specific']['crossref']['license'] = license_info
            
        # Extract subject/keywords
        if 'subject' in item and isinstance(item['subject'], list):
            paper['keywords'] = item['subject']
            
        # Store additional source-specific data that might be useful
        paper['source_specific']['crossref']['score'] = item.get('score')
        paper['source_specific']['crossref']['subtype'] = item.get('subtype')
        paper['source_specific']['crossref']['language'] = item.get('language')
        paper['source_specific']['crossref']['ISSN'] = item.get('ISSN')
        paper['source_specific']['crossref']['ISBN'] = item.get('ISBN')

        return paper

    async def get_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get paper metadata by DOI.
        
        Args:
            doi (str): DOI of the paper.
            
        Returns:
            Optional[Dict[str, Any]]: Paper metadata or None if not found.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/{doi}",
                params={'mailto': self.email},
                headers=self.headers
            ) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                if data and 'message' in data:
                    return self._parse_paper(data['message'])
                    
        return None 