"""
Semantic Scholar API interface for searching research papers.
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
import httpx
from datetime import datetime
from ..config import SEMANTIC_SCHOLAR_API_KEY

logger = logging.getLogger(__name__)

class SemanticScholarSearcher:
    """Semantic Scholar API searcher implementation."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    FIELDS = [
        "title",
        "abstract",
        "authors",
        "year",
        "journal",
        "publicationTypes",
        "externalIds",
        "url",
        "citationCount",
        "referenceCount",
        "isOpenAccess",
        "openAccessPdf",
        "fieldsOfStudy",
        "publicationDate"
    ]

    def __init__(self, api_key: Optional[str] = SEMANTIC_SCHOLAR_API_KEY):
        """Initialize the Semantic Scholar searcher."""
        self.api_key = api_key
        self.headers = {"x-api-key": api_key} if api_key else {}

    async def search(
        self,
        query: str,
        limit: int = 100,
        paper_types: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Semantic Scholar API.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            paper_types (Optional[List[str]]): List of paper types to include
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            until_date (Optional[str]): End date in YYYY-MM-DD format
            
        Returns:
            List[Dict[str, Any]]: List of paper metadata
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
        limit: int = 100,
        paper_types: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        **kwargs
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Search for papers and return both processed results and raw response.
        
        Args:
            Same as search method
            
        Returns:
            tuple: (processed_results, raw_response)
        """
        # Process query to make it more suitable for Semantic Scholar
        processed_query = self._process_query(query)
        logger.info(f"Original query: '{query}'")
        logger.info(f"Processed query for Semantic Scholar: '{processed_query}'")
        
        results = []
        offset = 0
        page_size = min(limit, 100)  # API limit is 100 per request
        all_raw_data = []  # Store all raw responses
        
        try:
            async with httpx.AsyncClient() as client:
                while offset < limit:
                    # Construct search URL with fields
                    url = f"{self.BASE_URL}/paper/search"
                    params = {
                        "query": processed_query,
                        "fields": ",".join(self.FIELDS),
                        "offset": offset,
                        "limit": page_size
                    }
                    
                    logger.info(f"Sending request to Semantic Scholar API: {url} with offset={offset}, limit={page_size}")
                    
                    # Make API request
                    response = await client.get(url, params=params, headers=self.headers)
                    
                    if response.status_code != 200:
                        logger.error(f"Error searching Semantic Scholar: {response.status_code} - {response.text}")
                        break
                        
                    data = response.json()
                    all_raw_data.append(data)  # Store raw response
                    
                    # Process results
                    papers = data.get("data", [])
                    if not papers:
                        logger.warning(f"No papers found in Semantic Scholar response for query: '{processed_query}'")
                        break
                        
                    logger.info(f"Received {len(papers)} papers from Semantic Scholar API")
                    
                    # Parse each paper
                    parsed_count = 0
                    for paper in papers:
                        parsed = self._parse_paper(paper)
                        if parsed:
                            # Apply date filter if specified
                            if from_date or until_date:
                                pub_date = parsed.get("published")
                                if pub_date:
                                    try:
                                        pub_dt = datetime.strptime(pub_date, "%Y-%m-%d")
                                        if from_date and pub_dt < datetime.strptime(from_date, "%Y-%m-%d"):
                                            continue
                                        if until_date and pub_dt > datetime.strptime(until_date, "%Y-%m-%d"):
                                            continue
                                    except ValueError:
                                        logger.warning(f"Could not parse date: {pub_date}")
                            results.append(parsed)
                            parsed_count += 1
                            
                    logger.info(f"Successfully parsed {parsed_count} papers")
                    
                    # Update offset for next page
                    offset += len(papers)
                    if len(papers) < page_size:
                        break
                        
            # Combine all raw responses into one object
            combined_raw = {
                "query": query,
                "processed_query": processed_query,
                "limit": limit,
                "total_results": len(results),
                "pages": all_raw_data
            }
            
            return results[:limit], combined_raw
            
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {str(e)}")
            return [], {"query": query, "processed_query": processed_query, "error": str(e)}
            
    def _process_query(self, query: str) -> str:
        """
        Process a natural language query into a format better suited for Semantic Scholar.
        
        Args:
            query (str): Original query, possibly in natural language
            
        Returns:
            str: Processed query optimized for Semantic Scholar
        """
        # If query is already short (likely keywords), return as is
        if len(query.split()) <= 6:
            return query
            
        # For longer queries, extract key terms
        # Remove common question words and stop words
        question_words = ["what", "why", "how", "when", "where", "which", "who", "are", "is", "the", "of", "in", "on", "at", "to", "for", "with", "by", "about", "like", "through", "over", "before", "between", "after", "since", "without", "under", "within", "along", "following", "across", "behind", "beyond", "plus", "except", "but", "up", "out", "around", "down", "off", "above", "near"]
        
        # Split query into words and filter out question words and stop words
        words = query.lower().split()
        keywords = [word for word in words if word not in question_words and len(word) > 2]
        
        # If we have too few keywords, use the original query
        if len(keywords) < 3:
            return query
            
        # Join keywords back into a query string
        return " ".join(keywords)

    def _parse_paper(self, paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse paper metadata from API response."""
        try:
            # Get DOI if available
            external_ids = paper.get("externalIds", {})
            doi = external_ids.get("DOI")
            if not doi:
                return None
                
            # Extract basic metadata
            metadata = {
                "doi": doi,
                "title": paper.get("title"),
                "abstract": paper.get("abstract"),
                "authors": [author.get("name") for author in paper.get("authors", []) if author.get("name")],
                "year": paper.get("year"),
                "published": paper.get("publicationDate"),
                "url": paper.get("url"),
                "citations_count": paper.get("citationCount"),
                "references_count": paper.get("referenceCount"),
                "is_open_access": paper.get("isOpenAccess", False),
                "fields_of_study": paper.get("fieldsOfStudy", []),
                
                # Add additional fields
                "volume": None,
                "issue": None,
                "pages": None,
                "publication_date": paper.get("publicationDate"),  # Already included above, but added for consistency
                "publication_types": paper.get("publicationTypes", []),
                "keywords": [],  # Semantic Scholar doesn't provide keywords directly
                "pmid": external_ids.get("PubMed"),
                "pmc_id": external_ids.get("PubMedCentral"),
                "corpus_id": external_ids.get("CorpusId"),
                "source_specific": {
                    "semantic_scholar": {
                        "paper_id": paper.get("paperId"),
                        "external_ids": external_ids
                    }
                }
            }
            
            # Add journal name if available
            if isinstance(paper.get("journal"), dict):
                metadata["journal"] = paper["journal"].get("name")
                
                # Extract volume and pages from journal info
                metadata["volume"] = paper["journal"].get("volume")
                metadata["pages"] = paper["journal"].get("pages")
            
            # Add open access PDF if available
            if isinstance(paper.get("openAccessPdf"), dict):
                metadata["open_access_pdf"] = paper["openAccessPdf"].get("url")
                # Store open access status in source_specific
                metadata["source_specific"]["semantic_scholar"]["open_access_status"] = paper["openAccessPdf"].get("status")
                
            # Add influential citation count if available
            if "influentialCitationCount" in paper:
                metadata["source_specific"]["semantic_scholar"]["influential_citation_count"] = paper["influentialCitationCount"]
                
            # Add TLDR (AI-generated summary) if available
            if isinstance(paper.get("tldr"), dict) and paper["tldr"].get("text"):
                metadata["source_specific"]["semantic_scholar"]["tldr"] = paper["tldr"].get("text")
                
            # Add venue information if available
            if paper.get("venue"):
                metadata["source_specific"]["semantic_scholar"]["venue"] = paper.get("venue")
                
            return metadata
            
        except Exception as e:
            logger.error(f"Error parsing paper metadata: {str(e)}")
            return None

    async def get_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper metadata by Semantic Scholar paper ID.
        
        Args:
            paper_id (str): Semantic Scholar paper ID.
            
        Returns:
            Optional[Dict[str, Any]]: Paper metadata or None if not found.
        """
        try:
            # Use asyncio.to_thread to run synchronous API call in a separate thread
            paper = await asyncio.to_thread(
                self.client.get_paper,
                paper_id
            )
            
            return self._parse_paper(paper) if paper else None

        except Exception as e:
            logger.error(f"Error fetching paper ID {paper_id}: {str(e)}")
            return None 