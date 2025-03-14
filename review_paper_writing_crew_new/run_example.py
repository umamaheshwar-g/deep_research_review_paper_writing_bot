"""
Run an example review paper generation on a specific topic.
"""

import os
import sys
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Check if API keys are set
if not os.getenv("OPENAI_API_KEY") or not os.getenv("PINECONE_API_KEY"):
    print("Error: OPENAI_API_KEY and PINECONE_API_KEY must be set in .env file")
    print("Please copy .env.example to .env and fill in your API keys")
    sys.exit(1)

# Import main function
from main import main

# Set up command line arguments
import sys
import argparse

# Create a parser with default values
parser = argparse.ArgumentParser(description='Generate a research review paper.')
parser.add_argument('--topic', type=str, default="Diffusion Large Language Models", 
                    help='The research topic to review')
parser.add_argument('--output', type=str, default='review_paper.md', 
                    help='Output filename')
parser.add_argument('--namespace', type=str, default=None, 
                    help='Pinecone namespace (UUID will be generated if not provided)')

# Parse arguments
args = parser.parse_args()

print("=" * 80)
print(f"Starting review paper generation on topic: {args.topic}")
print(f"Output will be saved to: {args.output}")
print("=" * 80)

# Override sys.argv to pass these arguments to main.py
sys.argv = [
    'main.py',
    f'--topic={args.topic}',
    f'--output={args.output}'
]
if args.namespace:
    sys.argv.append(f'--namespace={args.namespace}')

# Run the main function
if __name__ == "__main__":
    main() 