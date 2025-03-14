import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

# Load environment variables
load_dotenv()

def check_namespace_metadata(namespace):
    """Check the metadata in a Pinecone namespace."""
    # Initialize Pinecone
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        print("Error: PINECONE_API_KEY not found in environment variables")
        return
        
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index("deepresearchreviewbot")
    
    # Get index stats
    try:
        stats = index.describe_index_stats()
        
        # Check if namespace exists
        if 'namespaces' in stats and namespace in stats['namespaces']:
            vector_count = stats['namespaces'][namespace].get('vector_count', 0)
            print(f"Namespace '{namespace}' exists with {vector_count} vectors.")
        else:
            print(f"Namespace '{namespace}' does not exist.")
            return
    except Exception as e:
        print(f"Error getting index stats: {str(e)}")
        return
    
    # Query the namespace to get sample vectors
    try:
        # Create a dummy embedding for querying
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("Error: OPENAI_API_KEY not found in environment variables")
            return
            
        client = OpenAI(api_key=openai_api_key)
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=["sample query"]
        )
        query_embedding = response.data[0].embedding
        
        # Query the index
        results = index.query(
            namespace=namespace,
            vector=query_embedding,
            top_k=5,
            include_values=False,
            include_metadata=True
        )
        
        if not results or not results.get('matches'):
            print("No results found in the namespace.")
            return
        
        # Check metadata fields
        print("\nMetadata fields in the first result:")
        first_match = results['matches'][0]
        metadata = first_match.get('metadata', {})
        
        for key, value in metadata.items():
            print(f"  {key}: {type(value).__name__} = {value}")
        
        # Check specifically for citation field
        if 'citation' in metadata:
            print("\nCitation field exists with value:", metadata['citation'])
        else:
            print("\nCitation field is missing from metadata!")
            
        # Print all metadata for inspection
        print("\nFull metadata of first result:")
        print(json.dumps(metadata, indent=2))
        
    except Exception as e:
        print(f"Error querying namespace: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python check_pinecone.py <namespace_uuid>")
        sys.exit(1)
    
    namespace = sys.argv[1]
    check_namespace_metadata(namespace) 