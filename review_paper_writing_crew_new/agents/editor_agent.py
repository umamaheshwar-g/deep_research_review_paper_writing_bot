from crewai import Agent
from typing import List
from crewai.tools import BaseTool

def create_editor_agent(tools: List[BaseTool] = None):
    """Create the editor agent that reviews and refines the review paper.
    
    This agent is specialized in:
    - Verifying proper citation usage
    - Checking content relevance and organization
    - Ensuring proper chunk context maintenance
    - Validating academic writing standards
    - Maintaining narrative coherence
    
    Returns:
        Agent: The configured editor agent
    """
    
    return Agent(
        role="Academic Editor",
        goal="""Review and refine the review paper to ensure clarity, coherence, and academic rigor.
        Verify proper citation usage and content organization based on relevance.
        Ensure proper use of content chunks, citations, and relevance scoring.
        ou will maintain and track intext citations in the format used for APA style along with the reference list. Track local ids of references to better retrive relevant chunks when you have followup questions.""",
        backstory="""You are a seasoned academic editor with expertise in reviewing 
        content derived from chunked research papers. You excel at:
        - Verifying proper citation usage and formatting
        - Ensuring content is organized effectively based on relevance
        - Checking that information from different chunks flows coherently
        - Validating that high-relevance content is appropriately emphasized
        - Maintaining academic writing standards and clarity
        
        Your editing focuses on both technical accuracy and readability, ensuring that 
        information from various chunks is well-integrated and properly cited. You have 
        a keen eye for identifying gaps in citation coverage and ensuring that the most 
        relevant content is effectively presented.""",
        verbose=True,
        allow_delegation=False,
        llm_config={
            "model": "gpt-4o-mini",
            # "model": "o3-mini",
            "temperature": 0.2,
            "max_tokens": 8000
        },
        tools=tools or [],  # Editor uses the draft provided by the writer
    ) 