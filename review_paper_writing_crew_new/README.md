# Deep Research Review Paper Writing Crew

A multi-agent system built with CrewAI for automatically generating research review papers based on academic papers stored in a Pinecone vector database.

## Project Overview

This system uses a team of AI agents to:
1. Retrieve relevant research papers from a Pinecone vector database
2. Analyze and synthesize information from multiple papers
3. Structure and write comprehensive review papers
4. Edit and refine the final document

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   ```

## Usage

Run the main script to start the review paper writing process:

```
python main.py --topic "Your research topic" --output "output_filename.md"
```

## Project Structure

- `main.py`: Entry point for the application
- `agents/`: Contains definitions for all CrewAI agents
- `tools/`: Custom tools used by the agents
- `tasks/`: Task definitions for the CrewAI workflow
- `utils/`: Utility functions and helpers

## Customization

You can customize the review paper generation by modifying:
- The agent prompts in `agents/`
- The task definitions in `tasks/`
- The retrieval parameters in `tools/retriever.py` 