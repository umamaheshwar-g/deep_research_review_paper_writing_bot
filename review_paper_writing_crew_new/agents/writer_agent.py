from crewai import Agent
from typing import List
from crewai.tools import BaseTool

def create_writer_agent(tools: List[BaseTool] = None):
    """Create the writer agent that drafts the review paper.
    
    This agent is specialized in:
    - Working with chunked research content
    - Managing and formatting citations
    - Organizing content based on relevance scores
    - Synthesizing information across document chunks
    - Maintaining academic writing standards
    
    Args:
        tools (List[BaseTool], optional): Tools for the writer agent to use
        
    Returns:
        Agent: The configured writer agent
    """
    
    return Agent(
        role="Academic Writer",
        goal="""Write a comprehensive, well-structured review paper of 3000-6000 words based on the research findings.
        Ensure proper citation and content organization.""",
        backstory="""You are a talented academic writer with expertise in working with 
        findings. You excel at:
        - Synthesizing information from multiple document sections while maintaining context
        - Properly attributing sources using citation information
        - Creating coherent narratives content
        - Following academic writing conventions and standards
        - Preserve as much information as possible from the provided research content
        
        Your writing style is scholarly yet accessible, and you understand how to weave 
        together information from various chunks while maintaining proper citation tracking 
        and academic rigor. You can effectively use relevance scores to prioritize content 
        and create a well-structured narrative.""",
        verbose=True,
        allow_delegation=False,
        llm_config={
            # "model": "gpt-4",
            "model": "o3-mini",
            "temperature": 0.4,
            "max_tokens": 16000
        },
        tools=tools or [],
    ) 