"""
PubMed API interface for searching research papers.
"""

import asyncio
import aiohttp
import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..config import PUBMED_TOOL, PUBMED_EMAIL, DEFAULT_HEADERS
from ..utils.doi_validator import normalize_doi

logger = logging.getLogger(__name__)

class PubMedSearcher:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, tool: str = PUBMED_TOOL, email: str = PUBMED_EMAIL):
        """
        Initialize the PubMed searcher.
        
        Args:
            tool (str): Tool name for PubMed API.
            email (str): Email for PubMed API.
        """
        self.tool = tool
        self.email = email
        self.headers = DEFAULT_HEADERS.copy()

    async def search(
        self,
        query: str,
        limit: int = 100,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using PubMed API.
        
        Args:
            query (str): Search query.
            limit (int): Maximum number of results to return.
            from_date (Optional[str]): Start date in format YYYY-MM-DD.
            until_date (Optional[str]): End date in format YYYY-MM-DD.
            **kwargs: Additional arguments to pass to PubMed API.
            
        Returns:
            List[Dict[str, Any]]: List of paper metadata.
        """
        results, _ = await self.search_with_raw(
            query=query,
            limit=limit,
            from_date=from_date,
            until_date=until_date,
            **kwargs
        )
        return results
        
    async def search_with_raw(
        self,
        query: str,
        limit: int = 100,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        **kwargs
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Search for papers using PubMed API following the standard E-utilities workflow.
        
        Args:
            Same as search method.
            
        Returns:
            tuple: (processed_results, raw_response)
        """
        # Build date filter if needed
        date_filter = []
        if from_date:
            date_filter.append(f"{from_date}[PDAT]")
        if until_date:
            date_filter.append(f"{until_date}[PDAT]")

        # Build search query
        search_query = query
        if date_filter:
            search_query = f"({search_query}) AND ({' AND '.join(date_filter)})"

        logger.info(f"Searching PubMed with query: {search_query}")
        
        # Store all raw responses
        raw_responses = {
            'search_query': search_query,
            'esearch': None,
            'esummary': None,
            'efetch': None
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Use ESearch to get PMIDs - Using XML format
                esearch_url = f"{self.BASE_URL}/esearch.fcgi"
                esearch_params = {
                    'db': 'pubmed',
                    'term': search_query,
                    'retmax': limit,
                    'usehistory': 'y',  # Use history server to store results
                    'retmode': 'xml',  # Changed from 'json' to 'xml'
                    'tool': self.tool,
                    'email': self.email
                }
                
                logger.info(f"Sending ESearch request to PubMed: {esearch_url}")
                
                async with session.get(
                    esearch_url,
                    params=esearch_params,
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Error from PubMed ESearch API: {response.status}")
                        return [], raw_responses
                        
                    esearch_text = await response.text()
                    raw_responses['esearch'] = esearch_text
                    
                    # Parse XML response
                    try:
                        esearch_root = ET.fromstring(esearch_text)
                        
                        # Extract PMIDs
                        pmids = []
                        for id_elem in esearch_root.findall('.//IdList/Id'):
                            pmids.append(id_elem.text)
                        
                        # Extract WebEnv and QueryKey
                        webenv_elem = esearch_root.find('.//WebEnv')
                        webenv = webenv_elem.text if webenv_elem is not None else None
                        
                        querykey_elem = esearch_root.find('.//QueryKey')
                        query_key = querykey_elem.text if querykey_elem is not None else None
                        
                        if not pmids:
                            logger.info("No PMIDs found in PubMed search")
                            return [], raw_responses
                            
                        logger.info(f"Found {len(pmids)} PMIDs in PubMed search")
                    except Exception as e:
                        logger.error(f"Error parsing ESearch XML: {str(e)}")
                        return [], raw_responses
                
                # Step 2: Use EFetch to get full article data - Using XML format
                efetch_url = f"{self.BASE_URL}/efetch.fcgi"
                efetch_params = {
                    'db': 'pubmed',
                    'retmode': 'xml',
                    'tool': self.tool,
                    'email': self.email
                }
                
                # Use WebEnv/QueryKey if available, otherwise use PMIDs directly
                if webenv and query_key:
                    efetch_params['webenv'] = webenv
                    efetch_params['query_key'] = query_key
                    efetch_params['retmax'] = limit
                    logger.info(f"Using WebEnv/QueryKey for EFetch")
                else:
                    efetch_params['id'] = ','.join(pmids)
                    logger.info(f"Using PMIDs directly for EFetch")
                
                logger.info(f"Sending EFetch request to PubMed: {efetch_url}")
                
                async with session.get(
                    efetch_url,
                    params=efetch_params,
                    headers=self.headers
                ) as efetch_response:
                    if efetch_response.status != 200:
                        logger.error(f"Error from PubMed EFetch API: {efetch_response.status}")
                        return [], raw_responses
                        
                    # Get XML response
                    efetch_text = await efetch_response.text()
                    raw_responses['efetch'] = efetch_text
                    
                    # Parse XML to extract article data
                    try:
                        efetch_root = ET.fromstring(efetch_text)
                        articles = efetch_root.findall('.//PubmedArticle')
                        
                        if not articles:
                            logger.warning("No articles found in PubMed EFetch response")
                            return [], raw_responses
                            
                        logger.info(f"Retrieved {len(articles)} articles from PubMed")
                        
                        # Parse each article
                        results = []
                        for article in articles:
                            paper = self._parse_paper(article)
                            if paper:
                                results.append(paper)
                                
                        logger.info(f"Successfully parsed {len(results)} papers from PubMed")
                        return results, raw_responses
                    except Exception as e:
                        logger.error(f"Error parsing EFetch XML: {str(e)}")
                        return [], raw_responses
                    
        except Exception as e:
            logger.error(f"Error searching PubMed: {str(e)}")
            return [], raw_responses

    def _parse_paper(self, article) -> Optional[Dict[str, Any]]:
        """
        Parse paper metadata from PubMed XML.
        
        Args:
            article: PubMed article XML element.
            
        Returns:
            Optional[Dict[str, Any]]: Parsed paper metadata or None if invalid.
        """
        try:
            # Extract PMID
            pmid_elem = article.find('.//PMID')
            if pmid_elem is None:
                return None
            pmid = pmid_elem.text
            
            # Extract DOI
            doi = None
            pmc_id = None
            article_id_list = article.find('.//ArticleIdList')
            if article_id_list is not None:
                for article_id in article_id_list.findall('ArticleId'):
                    if article_id.get('IdType') == 'doi':
                        doi = article_id.text
                    elif article_id.get('IdType') == 'pmc':
                        pmc_id = article_id.text
            
            if not doi:
                return None
                
            # Normalize DOI
            doi = normalize_doi(doi)
            if not doi:
                return None

            # Extract title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else None
            
            # Extract abstract
            abstract_text = []
            abstract_elem = article.find('.//Abstract')
            if abstract_elem is not None:
                for abstract_part in abstract_elem.findall('.//AbstractText'):
                    label = abstract_part.get('Label')
                    text = abstract_part.text or ""
                    if label:
                        abstract_text.append(f"{label}: {text}")
                    else:
                        abstract_text.append(text)
            
            abstract = " ".join(abstract_text) if abstract_text else None
            
            # Extract authors
            authors = []
            author_list = article.find('.//AuthorList')
            if author_list is not None:
                for author_elem in author_list.findall('Author'):
                    last_name = author_elem.find('LastName')
                    fore_name = author_elem.find('ForeName')
                    
                    if last_name is not None and fore_name is not None:
                        author_name = f"{fore_name.text} {last_name.text}"
                        authors.append(author_name)
                    elif last_name is not None:
                        authors.append(last_name.text)
            
            # Extract publication date
            pub_date = None
            pub_date_elem = article.find('.//PubDate')
            if pub_date_elem is not None:
                year_elem = pub_date_elem.find('Year')
                month_elem = pub_date_elem.find('Month')
                day_elem = pub_date_elem.find('Day')
                
                year = year_elem.text if year_elem is not None else None
                month = month_elem.text if month_elem is not None else "01"
                day = day_elem.text if day_elem is not None else "01"
                
                if year:
                    # Convert month name to number if needed
                    try:
                        if month.isalpha():
                            month = datetime.strptime(month, '%b').month
                        pub_date = f"{year}-{int(month):02d}-{int(day):02d}"
                    except (ValueError, AttributeError):
                        pub_date = f"{year}-01-01"  # Default to January 1st if month parsing fails
            
            # Extract journal information
            journal_elem = article.find('.//Journal')
            journal_title = None
            volume = None
            issue = None
            if journal_elem is not None:
                journal_title_elem = journal_elem.find('.//Title')
                if journal_title_elem is not None:
                    journal_title = journal_title_elem.text
                
                # Extract volume and issue
                volume_elem = journal_elem.find('.//Volume')
                if volume_elem is not None:
                    volume = volume_elem.text
                
                issue_elem = journal_elem.find('.//Issue')
                if issue_elem is not None:
                    issue = issue_elem.text
            
            # Extract pagination
            pagination_elem = article.find('.//Pagination/MedlinePgn')
            pages = pagination_elem.text if pagination_elem is not None else None
            
            # Extract publication types
            publication_types = []
            pub_type_list = article.find('.//PublicationTypeList')
            if pub_type_list is not None:
                for pub_type in pub_type_list.findall('.//PublicationType'):
                    if pub_type.text:
                        publication_types.append(pub_type.text)
            
            # Extract keywords
            keywords = []
            keyword_list = article.find('.//KeywordList')
            if keyword_list is not None:
                for keyword in keyword_list.findall('.//Keyword'):
                    if keyword.text:
                        keywords.append(keyword.text)
            
            # Extract MeSH terms
            mesh_terms = []
            mesh_heading_list = article.find('.//MeshHeadingList')
            if mesh_heading_list is not None:
                for mesh_heading in mesh_heading_list.findall('.//MeshHeading'):
                    descriptor = mesh_heading.find('.//DescriptorName')
                    if descriptor is not None and descriptor.text:
                        mesh_terms.append(descriptor.text)
            
            # Create source-specific data
            source_specific = {
                'pubmed': {
                    'journal_iso_abbreviation': None,
                    'language': None,
                    'mesh_terms': mesh_terms,
                    'publication_types': publication_types,
                    'grant_info': []
                }
            }
            
            # Extract journal ISO abbreviation
            if journal_elem is not None:
                iso_abbrev_elem = journal_elem.find('.//ISOAbbreviation')
                if iso_abbrev_elem is not None:
                    source_specific['pubmed']['journal_iso_abbreviation'] = iso_abbrev_elem.text
            
            # Extract language
            language_elem = article.find('.//Language')
            if language_elem is not None:
                source_specific['pubmed']['language'] = language_elem.text
            
            # Extract grant information
            grant_list = article.find('.//GrantList')
            if grant_list is not None:
                for grant_elem in grant_list.findall('.//Grant'):
                    grant_info = {}
                    
                    grant_id_elem = grant_elem.find('.//GrantID')
                    if grant_id_elem is not None:
                        grant_info['grant_id'] = grant_id_elem.text
                    
                    agency_elem = grant_elem.find('.//Agency')
                    if agency_elem is not None:
                        grant_info['agency'] = agency_elem.text
                    
                    country_elem = grant_elem.find('.//Country')
                    if country_elem is not None:
                        grant_info['country'] = country_elem.text
                    
                    if grant_info:
                        source_specific['pubmed']['grant_info'].append(grant_info)
            
            # Build paper metadata
            paper = {
                'pmid': pmid,
                'doi': doi,
                'pmc_id': pmc_id,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'published': pub_date or year,  # Use full date if available, otherwise just year
                'publication_date': pub_date,  # Full date in YYYY-MM-DD format
                'journal': journal_title,
                'volume': volume,
                'issue': issue,
                'pages': pages,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                'publication_types': publication_types,
                'keywords': keywords,
                'source_specific': source_specific
            }
            
            return paper
            
        except Exception as e:
            logger.error(f"Error parsing PubMed paper: {str(e)}")
            return None

    def _parse_json_article(self, article_data: Dict[str, Any], pmid: str) -> Optional[Dict[str, Any]]:
        """
        Parse paper metadata from PubMed JSON.
        
        Args:
            article_data: PubMed article JSON data.
            pmid: PubMed ID.
            
        Returns:
            Optional[Dict[str, Any]]: Parsed paper metadata or None if invalid.
        """
        try:
            # Extract DOI
            doi = None
            article_ids = article_data.get('articleids', [])
            for article_id in article_ids:
                if article_id.get('idtype') == 'doi':
                    doi = article_id.get('value')
                    break
            
            if not doi:
                return None
                
            # Normalize DOI
            doi = normalize_doi(doi)
            if not doi:
                return None
                
            # Extract title
            title = article_data.get('title')
            
            # Extract abstract
            abstract = article_data.get('abstract')
            
            # Extract authors
            authors = []
            author_list = article_data.get('authors', [])
            for author in author_list:
                name = author.get('name')
                if name:
                    authors.append(name)
            
            # Extract publication date
            pub_date = None
            pub_date_str = article_data.get('pubdate')
            if pub_date_str:
                # Try to parse the date
                try:
                    # Handle various date formats
                    date_formats = [
                        '%Y %b %d',
                        '%Y %b',
                        '%Y'
                    ]
                    
                    for date_format in date_formats:
                        try:
                            date_obj = datetime.strptime(pub_date_str, date_format)
                            pub_date = date_obj.strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
                            
                    # If all formats fail, use year only
                    if not pub_date and re.search(r'\d{4}', pub_date_str):
                        year = re.search(r'\d{4}', pub_date_str).group(0)
                        pub_date = f"{year}-01-01"
                except Exception:
                    pass
            
            # Extract journal info
            journal = article_data.get('fulljournalname')
            
            # Generate URL from DOI
            url = f"https://doi.org/{doi}" if doi else None
            
            # Build paper metadata
            paper = {
                "doi": doi,
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "publication_date": pub_date,
                "journal": journal,
                "url": url,
                "source": "pubmed"
            }
            
            return paper
            
        except Exception as e:
            logger.error(f"Error parsing PubMed JSON article: {str(e)}")
            return None

    async def get_by_pmid(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Get paper metadata by PubMed ID.
        
        Args:
            pmid: PubMed ID.
            
        Returns:
            Optional[Dict[str, Any]]: Paper metadata or None if not found.
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Use EFetch to get article data
                efetch_url = f"{self.BASE_URL}/efetch.fcgi"
                efetch_params = {
                    'db': 'pubmed',
                    'id': pmid,
                    'retmode': 'xml',
                    'tool': self.tool,
                    'email': self.email
                }
                
                async with session.get(
                    efetch_url,
                    params=efetch_params,
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Error from PubMed EFetch API: {response.status}")
                        return None
                        
                    # Parse XML response
                    efetch_text = await response.text()
                    try:
                        efetch_root = ET.fromstring(efetch_text)
                        article = efetch_root.find('.//PubmedArticle')
                        
                        if article is None:
                            logger.warning(f"No article found for PMID: {pmid}")
                            return None
                            
                        return self._parse_paper(article)
                    except Exception as e:
                        logger.error(f"Error parsing EFetch XML: {str(e)}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting paper by PMID: {str(e)}")
            return None 