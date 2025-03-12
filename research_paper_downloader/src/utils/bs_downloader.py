"""
Utility for downloading PDFs from various sources using BeautifulSoup.
"""

import os
import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BSDownloader:
    """
    A utility class for downloading PDFs from various sources using BeautifulSoup.
    """
    
    def __init__(self, headers: Dict[str, str] = None):
        """
        Initialize the BSDownloader.
        
        Args:
            headers (Dict[str, str], optional): HTTP headers to use for requests.
        """
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def download_from_url(self, url: str, output_path: str) -> bool:
        """
        Download a PDF from a direct URL.
        
        Args:
            url (str): URL of the PDF.
            output_path (str): Path to save the PDF.
            
        Returns:
            bool: True if download was successful, False otherwise.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download from {url}: HTTP {response.status}")
                        return False
                    
                    # Check if the content is a PDF
                    content_type = response.headers.get('Content-Type', '')
                    content = await response.read()
                    
                    # Check if it's a PDF by content type or by examining the first few bytes
                    is_pdf = False
                    if 'application/pdf' in content_type:
                        is_pdf = True
                    elif content.startswith(b'%PDF-'):  # PDF files start with %PDF-
                        is_pdf = True
                    elif url.lower().endswith('.pdf') and len(content) > 1000 and not content.startswith(b'<!DOCTYPE html>') and not content.startswith(b'<html'):
                        # If URL ends with .pdf and content doesn't look like HTML, assume it's a PDF
                        is_pdf = True
                    
                    if not is_pdf:
                        logger.error(f"URL {url} does not contain a valid PDF (Content-Type: {content_type})")
                        return False
                    
                    # Download the file
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    
                    logger.info(f"Successfully downloaded PDF to {output_path}")
                    return True
        except Exception as e:
            logger.error(f"Error downloading from {url}: {str(e)}")
            return False
    
    async def find_pdf_link_from_page(self, url: str) -> Optional[str]:
        """
        Find a PDF link on a webpage.
        
        Args:
            url (str): URL of the webpage.
            
        Returns:
            Optional[str]: URL of the PDF if found, None otherwise.
        """
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        logger.error(f"Failed to access {url}: HTTP {response.status}")
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for PDF links with different strategies
                    
                    # 1. Look for meta tags with PDF links (highest priority)
                    meta_links = soup.find_all('meta', attrs={'name': ['citation_pdf_url', 'citation_fulltext_html_url', 'citation_fulltext_world_readable']})
                    
                    # 2. Look for links with PDF in the href
                    pdf_links = soup.find_all('a', href=lambda href: href and (
                        href.lower().endswith('.pdf') or 
                        '/pdf/' in href.lower() or 
                        'pdf' in href.lower() or
                        'fulltext' in href.lower()
                    ))
                    
                    # 3. Look for links with PDF-related text
                    pdf_text_links = soup.find_all('a', text=lambda text: text and (
                        'pdf' in text.lower() or 
                        'download' in text.lower() or 
                        'full text' in text.lower() or
                        'full article' in text.lower() or
                        'article pdf' in text.lower() or
                        'download article' in text.lower()
                    ))
                    
                    # 4. Publisher-specific patterns
                    publisher_patterns = {
                        'sciencedirect.com': {
                            'selector': 'a.pdf-download-btn-link, a.download-link, a.download-pdf-link',
                            'attribute': 'href'
                        },
                        'springer.com': {
                            'selector': 'a.download-article, a.download-pdf, a.c-pdf-download__link',
                            'attribute': 'href'
                        },
                        'ieee.org': {
                            'selector': 'a.doc-actions-link, a.stats-document-lh-action-downloadPdf_2, a[data-action="download"]',
                            'attribute': 'href'
                        },
                        'wiley.com': {
                            'selector': 'a.article-pdf-download, a.pdf-download, a[title*="PDF"]',
                            'attribute': 'href'
                        },
                        'pubmed.ncbi.nlm.nih.gov': {
                            'selector': 'a.link-item.pmc-link, a.link-item.bookshelf-link',
                            'attribute': 'href'
                        },
                        'semanticscholar.org': {
                            'selector': 'a[data-selenium-selector="paper-link"], a.download-button',
                            'attribute': 'href'
                        }
                    }
                    
                    # Combine all potential links
                    all_links = []
                    
                    # Add links from meta tags (highest priority)
                    for meta in meta_links:
                        content = meta.get('content')
                        if content:
                            all_links.append(urljoin(url, content))
                    
                    # Add links from publisher-specific patterns
                    for domain, pattern in publisher_patterns.items():
                        if domain in url:
                            publisher_links = soup.select(pattern['selector'])
                            for link in publisher_links:
                                href = link.get(pattern['attribute'])
                                if href:
                                    all_links.append(urljoin(url, href))
                    
                    # Add links from href attributes
                    for link in pdf_links:
                        href = link.get('href')
                        if href:
                            all_links.append(urljoin(url, href))
                    
                    # Add links from text links
                    for link in pdf_text_links:
                        href = link.get('href')
                        if href:
                            all_links.append(urljoin(url, href))
                    
                    # Filter and prioritize links
                    pdf_urls = []
                    seen_urls = set()
                    
                    for link in all_links:
                        # Skip duplicate URLs
                        if link in seen_urls:
                            continue
                        seen_urls.add(link)
                        
                        # Prioritize direct PDF links
                        if link.lower().endswith('.pdf'):
                            pdf_urls.insert(0, link)
                        # Prioritize links with /pdf/ in the path
                        elif '/pdf/' in link.lower():
                            pdf_urls.insert(len(pdf_urls) // 2, link)
                        else:
                            pdf_urls.append(link)
                    
                    # Return the first PDF link found
                    if pdf_urls:
                        logger.info(f"Found PDF link: {pdf_urls[0]}")
                        return pdf_urls[0]
                    
                    logger.warning(f"No PDF links found on {url}")
                    return None
        except Exception as e:
            logger.error(f"Error finding PDF link on {url}: {str(e)}")
            return None
    
    async def download_from_doi(self, doi: str, output_path: str) -> bool:
        """
        Download a paper using its DOI.
        
        Args:
            doi (str): DOI of the paper.
            output_path (str): Path to save the PDF.
            
        Returns:
            bool: True if download was successful, False otherwise.
        """
        # Normalize DOI
        doi = doi.strip().lower()
        if not doi.startswith('10.'):
            logger.error(f"Invalid DOI format: {doi}")
            return False
        
        # Try multiple approaches in order of preference
        
        # 1. Try to download from DOI URL
        logger.info(f"Attempting to download from DOI: {doi}")
        doi_url = f"https://doi.org/{doi}"
        
        try:
            # First, follow the DOI to the publisher's page
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(doi_url, allow_redirects=True) as response:
                    if response.status != 200:
                        logger.error(f"Failed to resolve DOI {doi}: HTTP {response.status}")
                    else:
                        # Get the publisher's URL
                        publisher_url = str(response.url)
                        logger.info(f"DOI {doi} resolved to {publisher_url}")
                        
                        # Find PDF link on the publisher's page
                        pdf_url = await self.find_pdf_link_from_page(publisher_url)
                        
                        if pdf_url:
                            # Download the PDF
                            success = await self.download_from_url(pdf_url, output_path)
                            if success:
                                return True
        except Exception as e:
            logger.error(f"Error following DOI {doi}: {str(e)}")
        
        # 2. Try alternative sources
        
        # 2.1 Try Unpaywall
        try:
            logger.info(f"Trying Unpaywall for DOI: {doi}")
            unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email=anonymous@example.com"
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(unpaywall_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('is_oa') and data.get('best_oa_location') and data['best_oa_location'].get('url_for_pdf'):
                            pdf_url = data['best_oa_location']['url_for_pdf']
                            logger.info(f"Found PDF via Unpaywall: {pdf_url}")
                            success = await self.download_from_url(pdf_url, output_path)
                            if success:
                                return True
        except Exception as e:
            logger.error(f"Error using Unpaywall for DOI {doi}: {str(e)}")
        
        # 2.2 Try arXiv if the DOI might be related to arXiv
        try:
            if 'arxiv' in doi:
                logger.info(f"Trying arXiv for DOI: {doi}")
                # Extract arXiv ID if present in the DOI
                arxiv_id = None
                if 'arxiv' in doi:
                    parts = doi.split('/')
                    for part in parts:
                        if part.isdigit() and len(part) == 4:  # Year part
                            if parts.index(part) + 1 < len(parts):
                                arxiv_id = parts[parts.index(part) + 1]
                                break
                
                if arxiv_id:
                    arxiv_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    logger.info(f"Trying arXiv URL: {arxiv_url}")
                    success = await self.download_from_url(arxiv_url, output_path)
                    if success:
                        return True
        except Exception as e:
            logger.error(f"Error using arXiv for DOI {doi}: {str(e)}")
        
        # 2.3 Try Semantic Scholar
        try:
            logger.info(f"Trying Semantic Scholar for DOI: {doi}")
            s2_url = f"https://api.semanticscholar.org/v1/paper/{doi}"
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(s2_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('url'):
                            pdf_url = await self.find_pdf_link_from_page(data['url'])
                            if pdf_url:
                                success = await self.download_from_url(pdf_url, output_path)
                                if success:
                                    return True
        except Exception as e:
            logger.error(f"Error using Semantic Scholar for DOI {doi}: {str(e)}")
        
        # 2.4 Try Sci-Hub as a last resort (if allowed)
        try:
            # Note: Using Sci-Hub may have legal implications in some jurisdictions
            # This is provided for educational purposes only
            logger.info(f"Trying alternative sources for DOI: {doi}")
            
            # List of potential Sci-Hub domains (these change frequently)
            scihub_domains = [
                "sci-hub.se", "sci-hub.st", "sci-hub.ru"
            ]
            
            for domain in scihub_domains:
                try:
                    scihub_url = f"https://{domain}/{doi}"
                    logger.info(f"Trying alternative source: {scihub_url}")
                    
                    pdf_url = await self.find_pdf_link_from_page(scihub_url)
                    if pdf_url:
                        success = await self.download_from_url(pdf_url, output_path)
                        if success:
                            return True
                except Exception as e:
                    logger.debug(f"Error with alternative source {domain} for DOI {doi}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error using alternative sources for DOI {doi}: {str(e)}")
        
        logger.error(f"All download methods failed for DOI: {doi}")
        return False
    
    async def download_from_semantic_scholar(self, paper_data: Dict[str, Any], output_path: str) -> bool:
        """
        Download a paper from Semantic Scholar data.
        
        Args:
            paper_data (Dict[str, Any]): Paper data from Semantic Scholar.
            output_path (str): Path to save the PDF.
            
        Returns:
            bool: True if download was successful, False otherwise.
        """
        # Try open_access_pdf first
        if paper_data.get('open_access_pdf'):
            logger.info(f"Attempting to download from open_access_pdf: {paper_data['open_access_pdf']}")
            success = await self.download_from_url(paper_data['open_access_pdf'], output_path)
            if success:
                return True
        
        # Try regular URL
        if paper_data.get('url'):
            logger.info(f"Attempting to find PDF from URL: {paper_data['url']}")
            pdf_url = await self.find_pdf_link_from_page(paper_data['url'])
            if pdf_url:
                return await self.download_from_url(pdf_url, output_path)
        
        # Try DOI as a last resort
        if paper_data.get('doi'):
            logger.info(f"Attempting to download using DOI: {paper_data['doi']}")
            return await self.download_from_doi(paper_data['doi'], output_path)
        
        logger.error("No valid download sources found in Semantic Scholar data")
        return False
    
    async def download_from_google_scholar(self, paper_data: Dict[str, Any], output_path: str) -> bool:
        """
        Download a paper from Google Scholar data.
        
        Args:
            paper_data (Dict[str, Any]): Paper data from Google Scholar.
            output_path (str): Path to save the PDF.
            
        Returns:
            bool: True if download was successful, False otherwise.
        """
        # Try pdf_url first
        if paper_data.get('pdf_url'):
            logger.info(f"Attempting to download from pdf_url: {paper_data['pdf_url']}")
            success = await self.download_from_url(paper_data['pdf_url'], output_path)
            if success:
                return True
        
        # Try regular URL
        if paper_data.get('url'):
            logger.info(f"Attempting to find PDF from URL: {paper_data['url']}")
            pdf_url = await self.find_pdf_link_from_page(paper_data['url'])
            if pdf_url:
                return await self.download_from_url(pdf_url, output_path)
        
        # Try DOI as a last resort
        if paper_data.get('doi'):
            logger.info(f"Attempting to download using DOI: {paper_data['doi']}")
            return await self.download_from_doi(paper_data['doi'], output_path)
        
        logger.error("No valid download sources found in Google Scholar data")
        return False
    
    async def download_from_pubmed(self, paper_data: Dict[str, Any], output_path: str) -> bool:
        """
        Download a paper from PubMed data.
        
        Args:
            paper_data (Dict[str, Any]): Paper data from PubMed.
            output_path (str): Path to save the PDF.
            
        Returns:
            bool: True if download was successful, False otherwise.
        """
        # Try DOI first
        if paper_data.get('doi'):
            logger.info(f"Attempting to download using DOI: {paper_data['doi']}")
            success = await self.download_from_doi(paper_data['doi'], output_path)
            if success:
                return True
        
        # Try PubMed URL
        if paper_data.get('pmid'):
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{paper_data['pmid']}/"
            logger.info(f"Attempting to find PDF from PubMed URL: {pubmed_url}")
            pdf_url = await self.find_pdf_link_from_page(pubmed_url)
            if pdf_url:
                return await self.download_from_url(pdf_url, output_path)
        
        logger.error("No valid download sources found in PubMed data")
        return False 