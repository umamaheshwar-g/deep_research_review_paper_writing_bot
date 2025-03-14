import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pinecone import Pinecone
from openai import OpenAI

class PineconeRetrieverInput(BaseModel):
    """Schema for PineconeRetriever tool inputs."""
    query: str = Field(description="The search query text")
    local_id: Optional[str] = Field(default=None, description="Document ID to search within a specific document")
    section_range: Optional[List[float]] = Field(
        default=None,
        description="Start and end percentages for section search as [start, end], e.g. [0.0, 0.15] for first 15%"
    )
    min_score: float = Field(default=0.0, description="Minimum relevance score threshold (0.0 to 1.0)")
    top_k: int = Field(default=5, description="Number of results to return")

class PineconeRetriever(BaseTool):
    """Tool for retrieving information from Pinecone vector database using chunk-based schema."""
    
    name: str = "PineconeRetriever"
    description: str = """Retrieves relevant research paper information from a Pinecone vector database.
    You can search across all documents or within specific documents/sections.
    
    To use this tool, provide:
    - query: Your search query text (required)
    - local_id: (optional) Document ID to search within a specific research paper
    - section_range: (optional) Provide start and end percentages as a list
      For example: [0.0, 0.15] for first 15%, [0.85, 1.0] for last 15%
      Common sections (but you can adjust percentages based on the paper structure):
      - Introduction: typically first 10-20%
      - Methodology: typically 15-45%
      - Results: typically 35-75%
      - Discussion: typically 65-90%
      - Conclusion: typically last 10-20%
    - min_score: (optional) Minimum relevance score (0.0 to 1.0), default: 0.0
    - top_k: (optional) Number of results to return, default: 5
    """
    
    args_schema: type[BaseModel] = PineconeRetrieverInput
    
    def __init__(self, namespace: str, index_name: str = "deepresearchreviewbot", debug: bool = True):
        """Initialize the PineconeRetriever tool."""
        super().__init__()
        self._namespace = namespace
        self._index_name = index_name
        self._debug = debug
        self._debug_file = self._setup_debug_file()
        
        # Initialize Pinecone and OpenAI clients
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not pinecone_api_key or not openai_api_key:
            raise ValueError("PINECONE_API_KEY or OPENAI_API_KEY not found in environment variables")
        
        self._pc = Pinecone(api_key=pinecone_api_key)
        self._openai_client = OpenAI(api_key=openai_api_key)
        self._index = self._pc.Index(self._index_name)
        
        self._log_debug("Initialized PineconeRetriever")

    def _setup_debug_file(self) -> Path:
        """Set up debug log file with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_dir = Path("debug_logs")
        debug_dir.mkdir(exist_ok=True)
        return debug_dir / f"retriever_debug_{timestamp}.log"

    def _log_debug(self, message: str, data: Any = None) -> None:
        """Log debug information to file if debug is enabled."""
        if not self._debug:
            return
            
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "message": message,
            "data": data
        }
        
        with open(self._debug_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, default=str) + "\n")

    def _get_chunk_range(self, section_range: List[float], total_chunks: int) -> Tuple[int, int]:
        """Calculate absolute chunk numbers from percentage range."""
        start_pct, end_pct = section_range
        # Ensure percentages are within valid range
        start_pct = max(0.0, min(1.0, start_pct))
        end_pct = max(0.0, min(1.0, end_pct))
        
        # Calculate absolute chunk numbers
        start_chunk = int(start_pct * total_chunks)
        end_chunk = int(end_pct * total_chunks)
        
        return start_chunk, end_chunk

    def run(self, tool_input: Union[str, Dict[str, Any]]) -> str:
        """Execute the tool with the given input."""
        self._log_debug("Tool execution started", {"input": tool_input})
        
        try:
            # Handle string input as just a query
            if isinstance(tool_input, str):
                self._log_debug("Processing string input as query")
                result = self._run(query=tool_input)
            else:
                # Handle dict input with full parameters
                self._log_debug("Processing dictionary input")
                result = self._run(
                    query=tool_input.get("query"),
                    local_id=tool_input.get("local_id"),
                    section_range=tool_input.get("section_range"),
                    min_score=tool_input.get("min_score", 0.0),
                    top_k=tool_input.get("top_k", 5)
                )
            
            self._log_debug("Tool execution completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error executing tool: {str(e)}"
            self._log_debug("Tool execution failed", {"error": error_msg})
            return error_msg
    
    def _run(
        self,
        query: str,
        local_id: Optional[str] = None,
        section_range: Optional[List[float]] = None,
        min_score: float = 0.0,
        top_k: int = 5
    ) -> str:
        """Internal method to run the tool with parsed parameters."""
        try:
            self._log_debug("Getting query embedding", {"query": query})
            # Get query embedding from OpenAI
            response = self._openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=[query]
            )
            query_embedding = response.data[0].embedding
            
            # Build filter dictionary
            filter_dict = {}
            filter_conditions = []
            
            # Add min_score filter if specified
            if min_score > 0:
                filter_conditions.append({"score": {"$gte": min_score}})
            
            # Add local_id filter if specified
            if local_id:
                filter_conditions.append({"local_id": local_id})
            
            # Add section range filter if specified
            if section_range and len(section_range) == 2:
                # Query to get a sample document to determine total chunks
                total_chunks = None
                sample_results = self._index.query(
                    namespace=self._namespace,
                    vector=query_embedding,
                    top_k=1,
                    include_metadata=True
                )
                if sample_results.get('matches'):
                    total_chunks = sample_results['matches'][0]['metadata'].get('total_chunks')
                
                if total_chunks:
                    start_chunk, end_chunk = self._get_chunk_range(section_range, total_chunks)
                    filter_conditions.append({"chunk_id": {"$gte": start_chunk}})
                    filter_conditions.append({"chunk_id": {"$lt": end_chunk}})
            
            # Combine all filter conditions with $and operator if there are any
            if filter_conditions:
                filter_dict = {"$and": filter_conditions}
            
            self._log_debug("Querying Pinecone", {
                "namespace": self._namespace,
                "top_k": top_k,
                "filter": filter_dict
            })
            
            # Query the Pinecone index
            results = self._index.query(
                namespace=self._namespace,
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                include_values=True,
                include_metadata=True
            )
            
            self._log_debug("Query completed", {"num_results": len(results.get('matches', []))})
            
            # Format and return the results
            return self._format_results(results)
            
        except Exception as e:
            error_msg = f"Error querying Pinecone: {str(e)}"
            self._log_debug("Query failed", {"error": error_msg})
            return error_msg
    
    def _format_results(self, results: Dict[str, Any], max_snippet_length: int = 300) -> str:
        """Format Pinecone query results for display using our schema fields.
        
        Args:
            results (Dict[str, Any]): The query results from Pinecone
            max_snippet_length (int): Maximum length for text snippets
            
        Returns:
            str: Formatted results string
        """
        if not results or not results.get('matches'):
            return "No results found."
        
        formatted = []
        for i, match in enumerate(results['matches']):
            similarity_score = match['score']  # Pinecone's similarity score
            metadata = match['metadata']
            
            # Extract all metadata fields
            local_id = metadata.get('local_id', 'Unknown')
            chunk_id = metadata.get('chunk_id', '?')
            total_chunks = metadata.get('total_chunks', '?')
            citation = metadata.get('citation', 'No citation available')
            relevance_score = metadata.get('score', 0.0)  # Custom relevance score
            text = metadata.get('text', '')
            
            # Format the result entry
            result = [
                f"Result {i+1}:",
                f"Document local id and chunk numers are: {local_id} (Chunk {chunk_id} of {total_chunks})",
                f"Relevance: {relevance_score:.3f} | Similarity: {similarity_score:.3f}",
                f"Source and citation/reference to be used in the review paper: {citation}, tracking this is prederred",
                "\nContent:",
                "=" * 10
            ]
            
            # Format the text content with truncation if needed
            if text:
                if len(text) > max_snippet_length:
                    text = text[:max_snippet_length] + "..."
                result.append(text)
            else:
                result.append("No text content available")
            
            formatted.append("\n".join(result))
        
        return "\n\n" + "-" * 80 + "\n\n".join(formatted) 

"""
PINECONE METADATA FILTERING REFERENCE

Pinecone supports filtering vectors during queries based on their associated metadata.
Below is a reference for the metadata filtering syntax:

Basic Operators:
- $eq: Equal to
- $ne: Not equal to
- $gt: Greater than
- $gte: Greater than or equal to
- $lt: Less than
- $lte: Less than or equal to
- $in: In array
- $nin: Not in array

Logical Operators:
- $and: Logical AND of multiple conditions
- $or: Logical OR of multiple conditions

Examples:

1. Simple equality:
   {"genre": "sci-fi"}

2. Numeric comparison:
   {"year": {"$gte": 2020}}

3. Multiple conditions with AND:
   {"$and": [
     {"genre": "sci-fi"},
     {"year": {"$gte": 2020}}
   ]}

4. Multiple conditions with OR:
   {"$or": [
     {"genre": "sci-fi"},
     {"genre": "fantasy"}
   ]}

5. Nested conditions:
   {"$and": [
     {"$or": [
       {"genre": "sci-fi"},
       {"genre": "fantasy"}
     ]},
     {"year": {"$gte": 2020}}
   ]}

6. Array operations:
   {"tags": {"$in": ["ai", "machine-learning"]}}

Best Practices:
- Keep metadata fields small and focused
- Use appropriate data types (strings, numbers, booleans)
- Index only metadata fields you plan to filter on
- Avoid deeply nested structures
- Consider cardinality (number of unique values) for performance

For more details, see: https://docs.pinecone.io/guides/data/understanding-metadata
""" 