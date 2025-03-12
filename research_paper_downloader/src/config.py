"""
Configuration settings for the research paper finder.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
def find_root_dir():
    """Find the project root directory containing the .env file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while current_dir != os.path.dirname(current_dir):  # Stop at root directory
        if os.path.exists(os.path.join(current_dir, '.env')):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return None

# Find and load .env file
root_dir = find_root_dir()
if root_dir:
    env_path = os.path.join(root_dir, '.env')
    print(f"Loading .env from: {env_path}")  # Debug print
    load_dotenv(env_path)
else:
    print("Warning: .env file not found in any parent directory")
    load_dotenv()  # Try loading from current directory

# Debug print environment variables (without sensitive values)
print(f"CROSSREF_EMAIL set: {bool(os.getenv('CROSSREF_EMAIL'))}")
print(f"PUBMED_EMAIL set: {bool(os.getenv('PUBMED_EMAIL'))}")
print(f"SEMANTIC_SCHOLAR_API_KEY set: {bool(os.getenv('SEMANTIC_SCHOLAR_API_KEY'))}")
print(f"SERPER_API_KEY set: {bool(os.getenv('SERPER_API_KEY'))}")
print(f"SERPER_DEV_API_KEY set: {bool(os.getenv('SERPER_DEV_API_KEY'))}")

# API Configuration
CROSSREF_EMAIL = os.getenv("CROSSREF_EMAIL")
if not CROSSREF_EMAIL or CROSSREF_EMAIL == "your_email@example.com":
    raise ValueError("CROSSREF_EMAIL not set in .env file")

PUBMED_TOOL = "ResearchPaperFinder"
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL")
if not PUBMED_EMAIL or PUBMED_EMAIL == "your_email@example.com":
    raise ValueError("PUBMED_EMAIL not set in .env file")

SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
if not SEMANTIC_SCHOLAR_API_KEY or SEMANTIC_SCHOLAR_API_KEY == "your_semantic_scholar_api_key":
    raise ValueError("SEMANTIC_SCHOLAR_API_KEY not set in .env file")

SERPER_API_KEY = os.getenv("SERPER_API_KEY") or os.getenv("SERPER_DEV_API_KEY")
if not SERPER_API_KEY:
    raise ValueError("Neither SERPER_API_KEY nor SERPER_DEV_API_KEY set in .env file")

# Download Settings
MAX_RETRIES = 3
TIMEOUT = 30
CONCURRENT_DOWNLOADS = 5
DEFAULT_OUTPUT_DIR = "downloads"

# Proxy Settings
USE_PROXIES = False
PROXY_TIMEOUT = 10

class ProxyConfig:
    def __init__(self, proxy_str: str):
        """Initialize proxy configuration from proxy string."""
        self.proxy_str = proxy_str
        self.http = f"http://{proxy_str}"
        self.https = f"http://{proxy_str}"

    def as_dict(self) -> Dict[str, str]:
        """Return proxy configuration as dictionary."""
        return {
            "http": self.http,
            "https": self.https
        }

# Search Settings
DEFAULT_SEARCH_LIMIT = 100
SUPPORTED_PAPER_TYPES = ["journal-article", "conference-paper", "preprint"]

# File paths and directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(BASE_DIR, DEFAULT_OUTPUT_DIR)

# Create download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# User agent for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Headers for requests
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Search sources - try sources in this order
SEARCH_SOURCES = [
    "crossref",          # Most comprehensive
    "semantic_scholar",  # Good for computer science
    "google_scholar",    # Additional source with good coverage
    "pubmed"             # Good for biomedical
] 