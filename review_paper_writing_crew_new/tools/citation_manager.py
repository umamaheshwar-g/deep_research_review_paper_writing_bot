import os
import json
from typing import Dict, Any, List, Optional
from crewai.tools import BaseTool

class CitationManager(BaseTool):
    """Tool for managing citations in the review paper."""
    
    name: str = "CitationManager"
    description: str = "Manages citations for the review paper, including formatting and organization."
    
    def __init__(self, citation_file: str = "citations.json"):
        """Initialize the CitationManager tool.
        
        Args:
            citation_file (str): The file to store citations in
        """
        super().__init__()
        self._citation_file = citation_file
        self._citations = self._load_citations()
    
    def _load_citations(self) -> Dict[str, Any]:
        """Load citations from the citation file.
        
        Returns:
            Dict[str, Any]: The loaded citations
        """
        if not os.path.exists(self._citation_file):
            return {}
        
        try:
            with open(self._citation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_citations(self) -> None:
        """Save citations to the citation file."""
        with open(self._citation_file, 'w', encoding='utf-8') as f:
            json.dump(self._citations, f, indent=2)
    
    def _run(self, action: str, citation_key: str = None, citation_data: Dict[str, Any] = None) -> str:
        """Run the tool to manage citations.
        
        Args:
            action (str): The action to perform (add, get, list, format)
            citation_key (str, optional): The key for the citation
            citation_data (Dict[str, Any], optional): The citation data to add
            
        Returns:
            str: The result of the action
        """
        if action == "add" and citation_key and citation_data:
            return self.add_citation(citation_key, citation_data)
        elif action == "get" and citation_key:
            return self.get_citation(citation_key)
        elif action == "list":
            return self.list_citations()
        elif action == "format" and citation_key:
            return self.format_citation(citation_key)
        elif action == "format_all":
            return self.format_all_citations()
        else:
            return "Invalid action or missing parameters."
    
    def add_citation(self, citation_key: str, citation_data: Dict[str, Any]) -> str:
        """Add a citation to the manager.
        
        Args:
            citation_key (str): The key for the citation
            citation_data (Dict[str, Any]): The citation data
            
        Returns:
            str: Success message
        """
        self._citations[citation_key] = citation_data
        self._save_citations()
        return f"Citation '{citation_key}' added successfully."
    
    def get_citation(self, citation_key: str) -> str:
        """Get a citation from the manager.
        
        Args:
            citation_key (str): The key for the citation
            
        Returns:
            str: The citation data or error message
        """
        if citation_key in self._citations:
            return json.dumps(self._citations[citation_key], indent=2)
        else:
            return f"Citation '{citation_key}' not found."
    
    def list_citations(self) -> str:
        """List all citations in the manager.
        
        Returns:
            str: List of citation keys
        """
        if not self._citations:
            return "No citations found."
        
        return "Citations:\n" + "\n".join(f"- {key}" for key in self._citations.keys())
    
    def format_citation(self, citation_key: str, style: str = "apa") -> str:
        """Format a citation in the specified style.
        
        Args:
            citation_key (str): The key for the citation
            style (str): The citation style to use
            
        Returns:
            str: The formatted citation or error message
        """
        if citation_key not in self._citations:
            return f"Citation '{citation_key}' not found."
        
        citation = self._citations[citation_key]
        
        if style.lower() == "apa":
            return self._format_apa(citation)
        else:
            return f"Citation style '{style}' not supported."
    
    def format_all_citations(self, style: str = "apa") -> str:
        """Format all citations in the specified style.
        
        Args:
            style (str): The citation style to use
            
        Returns:
            str: The formatted citations
        """
        if not self._citations:
            return "No citations found."
        
        formatted = []
        for key, citation in self._citations.items():
            if style.lower() == "apa":
                formatted.append(self._format_apa(citation))
            else:
                return f"Citation style '{style}' not supported."
        
        return "\n\n".join(formatted)
    
    def _format_apa(self, citation: Dict[str, Any]) -> str:
        """Format a citation in APA style.
        
        Args:
            citation (Dict[str, Any]): The citation data
            
        Returns:
            str: The formatted citation
        """
        # Extract citation data with defaults
        authors = citation.get("authors", "")
        year = citation.get("year", "")
        title = citation.get("title", "")
        journal = citation.get("journal", "")
        volume = citation.get("volume", "")
        issue = citation.get("issue", "")
        pages = citation.get("pages", "")
        doi = citation.get("doi", "")
        url = citation.get("url", "")
        
        # Format authors
        if isinstance(authors, list):
            if len(authors) == 1:
                author_str = authors[0]
            elif len(authors) == 2:
                author_str = f"{authors[0]} & {authors[1]}"
            else:
                author_str = f"{', '.join(authors[:-1])}, & {authors[-1]}"
        else:
            author_str = authors
        
        # Build citation
        citation_str = f"{author_str} ({year}). {title}."
        
        if journal:
            citation_str += f" *{journal}*"
            
            if volume:
                citation_str += f", {volume}"
                
                if issue:
                    citation_str += f"({issue})"
            
            if pages:
                citation_str += f", {pages}"
                
            citation_str += "."
        
        if doi:
            citation_str += f" https://doi.org/{doi}"
        elif url:
            citation_str += f" Retrieved from {url}"
        
        return citation_str 