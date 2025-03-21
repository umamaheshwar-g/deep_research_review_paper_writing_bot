from crewai import Agent
from typing import List
from crewai.tools import BaseTool

def create_researcher_agent(tools: List[BaseTool] = None):
    """To create a researcher agent that retrieves and analyzes research papers.
    
    This agent is specialized in:
    - Using semantic search to find relevant research chunks
    - Filtering results by relevance scores
    - Working with document chunks and their positions
    - Managing citations
    - Analyzing content across multiple documents
    
    Args:
        tools (List[BaseTool], optional): Tools for the researcher agent to use
        
    Returns:
        Agent: The configured researcher agent
    """
    
    return Agent(
        role="Research Paper Analyst",
        goal="""Find and retrive relevant research papers using pinecone retriever to extract key information in chunks for accomplisning tasks to write a comprehensive review paper.
        Focus on high-relevance content chunks and maintain proper citation tracking along with the local_id.""",
        backstory="""You are a meticulous research analyst with expertise in semantic search from Pinecone.
        You excel at:
        - Finding the most relevant chunks of information across research papers by providing semantic search queries.
        - Always track local_ids and use the local_id appropriately when you need to limit the scope of the research paper when more clarification is needed for deep research.
        - Use filtering strategies as applicable smartly based on .
        - Understanding document structure through chunk positions
        - Evaluating content relevance
        - Tracking and managing citations for academic integrity local_id for furthe deep reseach and referene
        - Synthesizing information from multiple sources while maintaining context
        - send intext citations in the format used for APA style.
        - send references in the exact format in context APA style.
        - only use the citations, references that are present as "Citation That you can use for this".
        
        """,
        verbose=True,
        allow_delegation=False,
        llm_config={
            # "model": "gpt-4o",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 8000
        },
        tools=tools or [],
    ) 
