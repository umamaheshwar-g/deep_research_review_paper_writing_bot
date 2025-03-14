# DeepResearchReviewBot Index Schema

## Index Configuration
- **Index Name**: deepresearchreviewbot
- **Embedding Model**: text-embedding-3-large (OpenAI)
- **Vector Dimension**: 3072 (OpenAI text-embedding-3-large dimension)
- **Metric**: cosine (default similarity metric)

## Vector Structure
Each vector in the index contains:

### ID Format
- Format: `{local_id}_{chunk_id}`
- Example: `paper123_0`, `paper123_1`

### Vector Values
- Embedding vector from OpenAI text-embedding-3-large model
- Dimension: 3072

### Metadata Fields
```json
{
    "total_pages": integer,
    "fetched_source": string,
    "local_id": string,
    "score": number,
    "citation": string,
    "reasoning": string,
    "chunk_id": integer,
    "total_chunks": integer,
    "page_start": integer,
    "page_end": integer
}
```

## Querying the Pinecone Index

### Basic Query Function
```python
from openai import OpenAI
import pinecone
import os

def query_pinecone(
    query: str, 
    namespace: str, 
    top_k: int = 5,
    filter_conditions: dict = None,
    score_threshold: float = None
) -> Dict[str, Any]:
    """
    Query the Pinecone index using semantic search.
    
    Args:
        query (str): The search query text
        namespace (str): The namespace to search in (usually the chat_id/session_id)
        top_k (int): Number of results to return (default: 5)
        filter_conditions (dict): Optional metadata filters
        score_threshold (float): Optional minimum similarity score threshold (0-1)
    
    Returns:
        Dict containing matches and their metadata
    """
    # Initialize Pinecone and OpenAI
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not pinecone_api_key or not openai_api_key:
        raise ValueError("PINECONE_API_KEY or OPENAI_API_KEY not found in environment variables")
        
    pc = pinecone.Pinecone(api_key=pinecone_api_key)
    client = OpenAI(api_key=openai_api_key)
    index = pc.Index("deepresearchreviewbot")
    
    # Get query embedding from OpenAI
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=[query]
        )
        query_embedding = response.data[0].embedding
    except Exception as e:
        raise Exception(f"Error getting embedding from OpenAI: {str(e)}")
    
    # Prepare query parameters
    query_params = {
        "namespace": namespace,
        "vector": query_embedding,
        "top_k": top_k,
        "include_values": True,
        "include_metadata": True
    }
    
    # Add filters if provided
    if filter_conditions:
        query_params["filter"] = filter_conditions
    
    # Query the index
    results = index.query(**query_params)
    
    # Apply score threshold if provided
    if score_threshold and results.matches:
        results.matches = [m for m in results.matches if m.score >= score_threshold]
    
    return results
```

### Advanced Query Examples

1. **Basic Search**
```python
# Simple semantic search
results = query_pinecone(
    query="What are the main advantages of transformer models?",
    namespace="session_123",
    top_k=5
)
```

2. **Filter by Page Range**
```python
# Search within specific pages
results = query_pinecone(
    query="What are the key findings?",
    namespace="session_123",
    filter_conditions={
        "page_start": {"$lte": 10},  # First 10 pages only
    }
)
```

3. **Filter by Score and Citation**
```python
# Search for highly-rated papers with citations
results = query_pinecone(
    query="transformer architecture improvements",
    namespace="session_123",
    filter_conditions={
        "score": {"$gte": 0.8},
        "citation": {"$exists": True}
    }
)
```

4. **Complex Metadata Filters**
```python
# Multiple conditions
results = query_pinecone(
    query="methodology section",
    namespace="session_123",
    filter_conditions={
        "$and": [
            {"total_pages": {"$gte": 10}},
            {"score": {"$gte": 0.7}},
            {"page_start": {"$lte": 5}}
        ]
    }
)
```

### Helper Function for Formatting Results

```python
def format_pinecone_results(results: Dict[str, Any], max_snippet_length: int = 300) -> str:
    """
    Format Pinecone query results for display.
    
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
        score = match['score']
        metadata = match['metadata']
        
        result = f"Result {i+1} (Score: {score:.4f}):\n"
        result += f"Document ID: {metadata.get('local_id', 'Unknown')}\n"
        result += f"Source: {metadata.get('fetched_source', 'Unknown')}\n"
        result += f"Pages: {metadata.get('page_start', '?')} - {metadata.get('page_end', '?')}\n"
        
        if metadata.get('citation'):
            result += f"Citation: {metadata['citation']}\n"
            
        if 'text' in match:
            text = match['text']
            if len(text) > max_snippet_length:
                text = text[:max_snippet_length] + "..."
            result += f"\nSnippet: {text}\n"
        
        formatted.append(result)
    
    return "\n" + "-" * 80 + "\n\n".join(formatted)
```

### Environment Setup
Required environment variables:
