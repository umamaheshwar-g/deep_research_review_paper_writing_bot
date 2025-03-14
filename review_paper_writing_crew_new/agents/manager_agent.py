from crewai import Agent
from typing import List
from crewai.tools import BaseTool

def create_manager_agent(tools: List[BaseTool] = None):
    """Create the manager agent that oversees the review paper writing process.
    
    This agent is specialized in:
    - Coordinating research content retrieval
    - Managing citation tracking
    - Ensuring proper content organization
    - Overseeing relevance-based filtering
    - Maintaining academic standards
    """
    
    return Agent(
        role="Research Review Manager",
        goal="""Coordinate the creation of a comprehensive, high-quality research review paper.
        Ensure proper use of content chunks, citations, and relevance scoring.
        ou will maintain and track intext citations in the format used for APA style along with the reference list. Track local ids of references to better retrive relevant chunks when you have followup questions.
        You will write a comprehensive detailed review paper based on research with a detailed introduction, methodology, results, discussion, and conclusion.""",
        backstory="""You are an experienced research director with expertise in managing 
        projects involving chunked research content. You excel at:
        - Coordinating the retrieval and analysis of relevant content chunks
        - Ensuring proper citation tracking and management
        - Overseeing content organization based on relevance scores
        - Managing the flow of information between team members
        - Maintaining high academic standards throughout the process

    

        Your organizational skills ensure that the team effectively uses the available 
        tools for semantic search, citation management, and content organization. You 
        understand how to prioritize high-relevance content while maintaining proper 
        academic rigor and citation standards.""",
        verbose=True,
        allow_delegation=True,
        # Using GPT-4 for the manager agent for better reasoning and coordination
        llm_config={
            # "model": "gpt-4o-mini",
            "model": "o3-mini",   
            "temperature": 0.2,
            "max_tokens": 8000
        },
        tools=tools or [],  # Manager uses the provided tools
    ) 