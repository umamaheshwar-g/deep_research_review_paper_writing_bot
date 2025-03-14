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

### Metadata Schema we can use for filtering
```json
{
    "local_id": "string",          // we can use For filtering, within this we can fetch for all chunks of a pdf with local_id
    "chunk_id": "integer",         // Position of the chunk within the document
    "total_chunks": "integer",     // Total number of chunks in the document using this we can

    "score": "float",             // Evaluation score (if available) will be between 0-1 1 meaning completely relevant to the topic we can use this for filtering, can use as filtering based on the section of the research review paper we are writing
    "citation": "string",         // Citation information we can use these APA citations and we will keep track of citations for references too
    // "reasoning": "string",        // Reasoning or notes about the document
    "text": "string"             // The actual text content of the chunk This is what we use to 
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
    query="What are the main advantages of transformer models?", # but we akk based on the research question and context
    namespace="your-session-uuid",
    top_k=5
)
```

### 2. Search Within a Specific Document
```python
# Search within a specific document using local_id
results = query_pinecone(
    query="What is the methodology used?",
    namespace="your-session-uuid",
    top_k=5,
    filter_dict={
        "local_id": "document123"
    }
)
```

### 3. Search with Score Filter
```python
# Search in highly-relevant chunks only
results = query_pinecone(
    query="What are the key findings?",
    namespace="your-session-uuid",
    top_k=5,
    filter_dict={
        "score": {"$gte": 0.8}
    }
)
```

### 4. Search in Document Introduction
```python
# Search in the beginning chunks of documents
results = query_pinecone(
    query="What is the research objective?",
    namespace="your-session-uuid",
    top_k=5,
    filter_dict={
        "$and": [
            {"chunk_id": {"$lte": 3}},  # First three chunks
            {"score": {"$gte": 0.7}}    # With high relevance
        ]
    }
)
```

### 5. Search in Document Conclusions
```python
# Search in the final chunks of documents
results = query_pinecone(
    query="What are the future research directions?",
    namespace="your-session-uuid",
    top_k=5,
    filter_dict={
        "$and": [
            {"chunk_id": -1},  # Last chunk
            {"score": {"$gte": 0.7}}
        ]
    }
)
```

### 6. Search with Citation Requirements
```python
# Search for chunks with specific citation patterns
results = query_pinecone(
    query="What are the findings from recent studies?",
    namespace="your-session-uuid",
    top_k=5,
    filter_dict={
        "$and": [
            {"citation": {"$exists": true}},  # Must have citations
            {"score": {"$gte": 0.75}} # if we want more, we will tailor it based on how much we want to explore
        ]
    }
)
```

### 7. Complex Multi-Document Search
```python
# Search across multiple documents with specific criteria
results = query_pinecone(
    query="Compare methodologies across studies",
    namespace="your-session-uuid",
    top_k=10,
    filter_dict={
        "$and": [
            {"score": {"$gte": 0.8}},
            {"chunk_id": {"$lte": {"$multiply": [0.3, "$total_chunks"]}}},  # First 30% of each document
            {"citation": {"$exists": true}}
        ]
    }
)
```

## Processing Results

```python
def format_pinecone_results(results: dict) -> str:
    """Format Pinecone query results for display.
    
    Formats results using the following metadata fields:
    - text: The content chunk
    - local_id: Document identifier
    - chunk_id: Position in document
    - total_chunks: Total chunks in document
    - citation: Citation information
    - score: Custom relevance score
    - match['score']: Pinecone similarity score
    """
    if not results or not results.get('matches'):
        return "No results found."
    
    formatted = []
    for i, match in enumerate(results['matches']):
        pinecone_score = match['score']  # Similarity score from Pinecone
        metadata = match['metadata']
        
        # Extract all relevant metadata
        text = metadata.get('text', '')
        local_id = metadata.get('local_id', 'Unknown')
        chunk_id = metadata.get('chunk_id', '?')
        total_chunks = metadata.get('total_chunks', '?')
        citation = metadata.get('citation', 'No citation available')
        relevance_score = metadata.get('score', 0.0)  # Custom relevance score
        
        # Format the result entry
        result = [
            f"Result {i+1}:",
            f"Document ID: {local_id}",
            f"Chunk: {chunk_id}/{total_chunks}",
            f"Relevance Score: {relevance_score:.3f}",
            f"Similarity Score: {pinecone_score:.3f}",
            f"Citation: {citation}",
            "\nContent:",
            "=" * 40
        ]
        
        # Format the text content with truncation if needed
        if text:
            max_length = 300
            if len(text) > max_length:
                text = text[:max_length] + "..."
            result.append(text)
        else:
            result.append("No text content available")
        
        formatted.append("\n".join(result))
    
    return "\n\n" + "-" * 80 + "\n\n".join(formatted)
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
