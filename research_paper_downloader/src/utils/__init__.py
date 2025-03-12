# Make utils a package 
from .bs_downloader import BSDownloader
from .proxy_manager import ProxyManager
from .doi_validator import is_valid_doi, normalize_doi, extract_doi

__all__ = [
    'BSDownloader',
    'ProxyManager',
    'is_valid_doi',
    'normalize_doi',
    'extract_doi'
] 