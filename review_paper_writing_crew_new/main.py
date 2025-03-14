# Must precede any llm module imports

from langtrace_python_sdk import langtrace

langtrace.init(api_key = 'b3972c908d04c709e6805d45e5fba780aacd5256e21614f4e543391f5edf8ec3')

import os
import argparse
import uuid
import sys
from dotenv import load_dotenv
from crewai import Crew, Agent, Task, Process

# Disable CrewAI emojis to prevent Unicode encoding issues on Windows
os.environ["CREWAI_DISABLE_EMOJI"] = "true"

# Import our custom agents
from agents.manager_agent import create_manager_agent
from agents.researcher_agent import create_researcher_agent
from agents.writer_agent import create_writer_agent
from agents.editor_agent import create_editor_agent

# Import our retriever tool
from tools.retriever import PineconeRetriever

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate a research review paper for a given topic in ')
    parser.add_argument('--topic', type=str, default="Diffusion Large Language Models", help='The research topic to review')
    parser.add_argument('--output', type=str, default='review_paper.md', help='Output filename')
    parser.add_argument('--namespace', type=str, default=None, help='Pinecone namespace (UUID will be generated if not provided)')
    parser.add_argument('--index-name', type=str, default="deepresearchreviewbot", help='Pinecone index name')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging for the retriever')
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Use the provided namespace or generate a new one
    namespace = args.namespace if args.namespace else str(uuid.uuid4())
    print(f"Using namespace: {namespace}")
    
    # Initialize the retriever tool
    # The PineconeRetriever has been simplified to use a more straightforward filtering approach
    # It supports filtering by local_id, section_range, and min_score without requiring a search_type
    retriever = PineconeRetriever(
        namespace=namespace,
        index_name=args.index_name,
        debug=args.debug
    )
    
    # Create agents
    manager = create_manager_agent()
    researcher = create_researcher_agent(tools=[retriever])
    writer = create_writer_agent() 
    editor = create_editor_agent()
    
    # Create tasks
    from tasks.research_tasks import create_research_tasks
    from tasks.writing_tasks import create_writing_tasks
    from tasks.editing_tasks import create_editing_tasks
    
    research_tasks = create_research_tasks(topic=args.topic, researcher=researcher)
    writing_tasks = create_writing_tasks(writer=writer)
    editing_tasks = create_editing_tasks(editor=editor)
    
    # Combine all tasks
    all_tasks = research_tasks + writing_tasks
    # all_tasks = research_tasks + writing_tasks + editing_tasks
    
    # Create the crew
    crew = Crew(
        agents=[manager, researcher, writer, editor],
        tasks=all_tasks,
        verbose=True,
        process=Process.sequential, # Tasks will be executed in the defined order
        memory=True
    )
    
    try:
        # Run the crew
        result = crew.kickoff()
        
        # Save the result to the output file
        with open(args.output, 'w', encoding='utf-8') as f:
            # Check if result is a CrewOutput object and extract the final output
            if hasattr(result, 'final_output'):
                f.write(result.final_output)
            elif hasattr(result, 'raw_output'):
                f.write(result.raw_output)
            else:
                # If it's a string or has a string representation, use that
                f.write(str(result))
        
        print(f"Review paper has been written and saved to {args.output}")
        return 0
    except Exception as e:
        print(f"Error generating review paper: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())