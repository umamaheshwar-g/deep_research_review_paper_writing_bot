"""
Example script demonstrating how to use the Deep Research Review Paper Writing Crew.
"""

import os
import sys
from dotenv import load_dotenv
from main import main

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Check if API keys are set
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("PINECONE_API_KEY"):
        print("Error: OPENAI_API_KEY and PINECONE_API_KEY must be set in .env file")
        print("Please copy .env.example to .env and fill in your API keys")
        exit(1)
    
    # Define the topic, output file, and namespace
    topic = "Recent Developments and challenges in Diffusion based Large Language Models dLLMS"
    output_file = "test_output_new8.md"
    namespace = "c7044b83-0783-44c0-bebe-aa433fd32498"
    
    print(f"Starting review paper generation on topic: {topic}")
    print(f"Output will be saved to: {output_file}")
    print(f"Using namespace: {namespace}")
    
    # Run the main function with explicit arguments
    sys.argv = [sys.argv[0], "--topic", topic, "--output", output_file, "--namespace", namespace]
    
    # Import main after setting sys.argv
    main() 