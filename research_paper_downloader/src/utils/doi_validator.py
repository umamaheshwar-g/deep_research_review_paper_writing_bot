"""
Utility functions for validating and handling DOIs.
"""

import re
from typing import Optional, Union
from urllib.parse import urlparse

# Regular expression for matching DOIs
DOI_PATTERN = r"^10\.\d{4,9}/[-._;()/:\w]+$"
DOI_URL_PATTERN = r"(?:https?://(?:dx\.)?doi\.org/|doi:|DOI:?\s*)(10\.\d{4,9}/[-._;()/:\w]+)"

def extract_doi(identifier: str) -> Optional[str]:
    """
    Extract DOI from a string that might be a DOI, URL, or other identifier.
    
    Args:
        identifier (str): The string to extract DOI from.
        
    Returns:
        Optional[str]: The extracted DOI if found, None otherwise.
    """
    # Clean up the input
    identifier = identifier.strip()
    
    # If it's already a valid DOI, return it
    if re.match(DOI_PATTERN, identifier):
        return identifier
    
    # Try to extract DOI from URL or DOI prefix
    match = re.search(DOI_URL_PATTERN, identifier)
    if match:
        return match.group(1)
    
    return None

def is_valid_doi(doi: str) -> bool:
    """
    Check if a string is a valid DOI.
    
    Args:
        doi (str): The DOI string to validate.
        
    Returns:
        bool: True if the DOI is valid, False otherwise.
    """
    return bool(re.match(DOI_PATTERN, doi))

def normalize_doi(doi: Union[str, None]) -> Optional[str]:
    """
    Normalize a DOI by extracting it from various formats and validating it.
    
    Args:
        doi (Union[str, None]): The DOI string to normalize.
        
    Returns:
        Optional[str]: The normalized DOI if valid, None otherwise.
    """
    if not doi:
        return None
        
    extracted_doi = extract_doi(doi)
    if extracted_doi and is_valid_doi(extracted_doi):
        return extracted_doi
    
    return None

def get_doi_url(doi: str) -> str:
    """
    Convert a DOI to its URL form.
    
    Args:
        doi (str): The DOI to convert.
        
    Returns:
        str: The DOI URL.
    """
    return f"https://doi.org/{doi}"

def is_doi_url(url: str) -> bool:
    """
    Check if a URL is a DOI URL.
    
    Args:
        url (str): The URL to check.
        
    Returns:
        bool: True if the URL is a DOI URL, False otherwise.
    """
    parsed = urlparse(url)
    return parsed.netloc in ['doi.org', 'dx.doi.org']

def extract_doi_from_url(url: str) -> Optional[str]:
    """
    Extract DOI from a URL.
    
    Args:
        url (str): URL that might contain a DOI.
        
    Returns:
        Optional[str]: Extracted DOI or None if not found.
    """
    if not url:
        return None
        
    # Common DOI patterns in URLs
    patterns = [
        r'doi\.org/([^/&?#]+)',
        r'doi/([^/&?#]+)',
        r'doi=([^/&?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
    return None 