import os
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Constants
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def query_pinecone_with_integrated_embedding(index_name: str, query: str, top_k: int = 5, api_key: str = None) -> Dict[str, Any]:
    """
    Query a Pinecone index with integrated embedding.
    
    Args:
        index_name (str): Name of the Pinecone index to query
        query (str): Query string
        top_k (int): Number of results to return
        api_key (str, optional): Pinecone API key
        
    Returns:
        Dict[str, Any]: Query results
    """
    # Use provided values or fall back to environment variables
    api_key = api_key or PINECONE_API_KEY
    
    if not api_key:
        raise ValueError("Pinecone API key not provided")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key)
    
    # Check if index exists
    index_names = [idx.name for idx in pc.list_indexes()]
    if index_name not in index_names:
        raise ValueError(f"Index '{index_name}' does not exist. Available indexes: {index_names}")
    
    # Connect to the index
    index = pc.Index(index_name)
    
    # Query the index with integrated embedding
    # The embedding will be generated automatically by Pinecone
    results = index.query(
        query_text=query,
        top_k=top_k,
        include_metadata=True
    )
    
    return results

def format_results(results: Dict[str, Any]) -> str:
    """
    Format query results for display.
    
    Args:
        results (Dict[str, Any]): Query results from Pinecone
        
    Returns:
        str: Formatted results
    """
    if not results or not results.get('matches'):
        return "No results found."
    
    formatted = []
    
    for i, match in enumerate(results['matches']):
        score = match['score']
        metadata = match['metadata']
        
        # Extract metadata fields
        local_id = metadata.get('local_id', 'Unknown')
        chunk_id = metadata.get('chunk_id', 'Unknown')
        title = metadata.get('title', 'Unknown Title')
        
        if isinstance(metadata.get('paper_metadata'), dict):
            paper_metadata = metadata['paper_metadata']
            authors = paper_metadata.get('authors', [])
            if isinstance(authors, list):
                authors = ', '.join(authors) if authors else 'Unknown'
        else:
            authors = 'Unknown'
        
        # Format citation if available
        citation = metadata.get('citation', '')
        
        # Format the result
        result = f"Result {i+1} (Score: {score:.4f}):\n"
        result += f"Document: {local_id} (Chunk {chunk_id})\n"
        result += f"Title: {title}\n"
        result += f"Authors: {authors}\n"
        
        if citation:
            result += f"Citation: {citation}\n"
        
        # Add evaluation data if available
        if 'evaluation' in metadata:
            eval_data = metadata['evaluation']
            result += f"Relevance Score: {eval_data.get('score', 'N/A')}/100\n"
            result += f"Reasoning: {eval_data.get('reasoning', 'N/A')}\n"
        
        # Add text snippet
        text = match.get('text', '')
        if not text:
            text = metadata.get('text', '')
        
        if text:
            # Truncate text if too long
            max_length = 300
            if len(text) > max_length:
                text = text[:max_length] + "..."
            result += f"\nSnippet: {text}\n"
        
        formatted.append(result)
    
    return "\n" + "-" * 80 + "\n\n".join(formatted)

def main():
    """Command line interface for querying Pinecone"""
    parser = argparse.ArgumentParser(description="Query a Pinecone index with integrated embedding")
    parser.add_argument("--index", required=True, help="Name of the Pinecone index to query")
    parser.add_argument("--query", required=True, help="Query string")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--api-key", help="Pinecone API key (defaults to PINECONE_API_KEY env var)")
    
    args = parser.parse_args()
    
    try:
        # Query Pinecone with integrated embedding
        results = query_pinecone_with_integrated_embedding(
            index_name=args.index,
            query=args.query,
            top_k=args.top_k,
            api_key=args.api_key
        )
        
        # Format and print results
        formatted_results = format_results(results)
        print(f"\nQuery: '{args.query}'")
        print(f"Index: {args.index}")
        print(f"Top {args.top_k} results:")
        print(formatted_results)
        
    except Exception as e:
        print(f"Error: {str(e)}")

# Function to be called from final_script.py
def query_index(index_name, query, top_k=5, api_key=None):
    """
    Function to be called from final_script.py to query an index.
    
    Args:
        index_name (str): Name of the Pinecone index to query
        query (str): Query string
        top_k (int): Number of results to return
        api_key (str, optional): Pinecone API key
        
    Returns:
        Dict[str, Any]: Query results and formatted string
    """
    try:
        results = query_pinecone_with_integrated_embedding(
            index_name=index_name,
            query=query,
            top_k=top_k,
            api_key=api_key
        )
        
        formatted_results = format_results(results)
        
        return {
            "raw_results": results,
            "formatted_results": formatted_results
        }
    except Exception as e:
        return {
            "error": str(e),
            "raw_results": None,
            "formatted_results": f"Error: {str(e)}"
        }

if __name__ == "__main__":
    main() 