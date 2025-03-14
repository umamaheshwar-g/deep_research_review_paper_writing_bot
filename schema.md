# Pinecone Vector Database Schema Documentation

## Connection Setup

```python
import os
from pinecone import Pinecone
from openai import OpenAI

# Initialize Pinecone
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)

# Connect to the index
index = pc.Index("deepresearchreviewbot")
```

## Schema Overview

### Vector Dimensions
- Model: text-embedding-3-large (OpenAI)
- Vector Dimension: 3072

### Metadata Schema
```json
{
    "local_id": "string",          // Unique identifier for the document
    "chunk_id": "integer",         // Position of the chunk within the document
    "total_chunks": "integer",     // Total number of chunks in the document
    "total_pages": "integer",      // Total number of pages in the document
    "page_start": "integer",       // Starting page number for this chunk
    "page_end": "integer",         // Ending page number for this chunk
    "fetched_source": "string",    // Source URL or identifier
    "score": "float",             // Evaluation score (if available)
    "citation": "string",         // Citation information
    "reasoning": "string",        // Reasoning or notes about the document
    "text": "string"             // The actual text content of the chunk
}
```

### Namespace Usage
- Each search session is assigned a unique UUID
- The UUID is used as the namespace in Pinecone
- This enables isolation between different search sessions

## Query Helper Function

```python
def query_pinecone(query: str, namespace: str, top_k: int = 5, 
                   filter_dict: dict = None, include_values: bool = True) -> dict:
    """
    Query the Pinecone index with various options.
    
    Args:
        query (str): The search query text
        namespace (str): The namespace to search in (session UUID)
        top_k (int): Number of results to return
        filter_dict (dict): Optional metadata filters
        include_values (bool): Whether to include vector values in response
        
    Returns:
        dict: Pinecone query response
    """
    # Initialize clients
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    index = pc.Index("deepresearchreviewbot")
    
    # Get query embedding
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=[query]
    )
    query_embedding = response.data[0].embedding
    
    # Query the index
    return index.query(
        namespace=namespace,
        vector=query_embedding,
        top_k=top_k,
        filter=filter_dict,
        include_values=include_values,
        include_metadata=True
    )
```

## Sample Queries

### 1. Basic Semantic Search
```python
# Simple search for most relevant chunks
results = query_pinecone(
    query="What are the main advantages of transformer models?",
    namespace="your-session-uuid",
    top_k=5
)
```

### 2. Search with Page Filters
```python
# Search only in the first 10 pages of documents
results = query_pinecone(
    query="What is the methodology used?",
    namespace="your-session-uuid",
    top_k=5,
    filter_dict={
        "page_start": {"$lte": 10}
    }
)
```

### 3. Search with Score Filter
```python
# Search in highly-rated documents only
results = query_pinecone(
    query="What are the key findings?",
    namespace="your-session-uuid",
    top_k=5,
    filter_dict={
        "score": {"$gte": 0.8}
    }
)
```

### 4. Complex Multi-condition Search
```python
# Search with multiple conditions
results = query_pinecone(
    query="What are the limitations discussed?",
    namespace="your-session-uuid",
    top_k=5,
    filter_dict={
        "$and": [
            {"score": {"$gte": 0.7}},
            {"page_start": {"$gte": 5}},
            {"page_end": {"$lte": 20}}
        ]
    }
)
```

### 5. Search in Specific Document Sections
```python
# Search in conclusion sections (typically last pages)
results = query_pinecone(
    query="What are the future research directions?",
    namespace="your-session-uuid",
    top_k=5,
    filter_dict={
        "$and": [
            {"page_end": {"$gte": {"$subtract": ["$total_pages", 3]}}},
            {"page_end": {"$lte": "$total_pages"}}
        ]
    }
)
```

## Processing Results

```python
def format_pinecone_results(results: dict) -> str:
    """Format Pinecone query results for display."""
    if not results or not results.get('matches'):
        return "No results found."
    
    formatted = []
    for i, match in enumerate(results['matches']):
        score = match['score']
        metadata = match['metadata']
        text = metadata.get('text', '')
        
        result = f"Result {i+1} (Score: {score:.4f}):\n"
        result += f"Document ID: {metadata.get('local_id', 'Unknown')}\n"
        result += f"Source: {metadata.get('fetched_source', 'Unknown')}\n"
        result += f"Pages: {metadata.get('page_start', '?')}-{metadata.get('page_end', '?')}\n"
        
        if text:
            max_length = 300
            if len(text) > max_length:
                text = text[:max_length] + "..."
            result += f"\nSnippet: {text}\n"
        
        formatted.append(result)
    
    return "\n" + "-" * 80 + "\n\n".join(formatted)
```

## Best Practices

1. **Namespace Management**
   - Use unique namespaces for different search sessions
   - Delete old namespaces when no longer needed
   - Consider implementing a TTL (Time To Live) for namespaces

2. **Query Optimization**
   - Use appropriate `top_k` values based on your needs
   - Implement filters to reduce search space
   - Consider using hybrid search (dense + sparse vectors) for better results

3. **Error Handling**
   - Always implement proper error handling for API calls
   - Handle rate limits and timeouts gracefully
   - Implement retries for failed requests

4. **Security**
   - Never expose API keys in code
   - Use environment variables for sensitive data
   - Implement proper access controls for different namespaces

5. **Performance**
   - Batch similar queries when possible
   - Cache frequently accessed results
   - Monitor and optimize index performance
