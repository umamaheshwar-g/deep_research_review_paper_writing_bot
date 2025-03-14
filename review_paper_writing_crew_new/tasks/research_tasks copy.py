from crewai import Task, Agent
from typing import List

def create_research_tasks(topic: str, researcher: Agent) -> List[Task]:
    """Create tasks for the research phase.
    
    Args:
        topic (str): The research topic
        researcher (Agent): The researcher agent
        
    Returns:
        List[Task]: The research tasks
    """
    
    # Task 1: Initial literature search
    initial_search = Task(
        description=f"""
        Conduct an initial search on the topic: "{topic}".
        
        Your task is to:
        1. Use the PineconeRetriever tool to find the most relevant papers on this topic
        2. Identify at least 10-15 key papers that should be included in the review
        3. For each paper, extract the title, authors, publication year, and a brief summary
        4. Organize the papers by relevance and importance to the topic
        5. Provide a report of your findings
        
        The output should be a structured list of papers with their key information and 
        a brief explanation of why each is important for the review.
        """,
        agent=researcher,
        expected_output="A structured list of 10-15 key papers with metadata and relevance assessment"
    )
    
    # Task 2: Identify key themes and concepts
    identify_themes = Task(
        description=f"""
        Based on the papers identified in the initial search, identify the key themes, 
        concepts, and research questions related to: "{topic}".
        
        Your task is to:
        1. Extract the main themes and concepts discussed across the papers
        2. Identify common methodologies used in the research
        3. Note any contradictions or debates in the literature
        4. Highlight gaps in the current research
        5. Suggest a conceptual framework for organizing the review
        
        The output should be a comprehensive analysis of the key themes and concepts 
        that will form the backbone of the review paper.
        """,
        agent=researcher,
        expected_output="A comprehensive analysis of key themes, concepts, methodologies, debates, and gaps",
        context=[initial_search]
    )
    
    # Task 3: Deep dive into methodologies
    methodology_analysis = Task(
        description=f"""
        Conduct a detailed analysis of the methodologies used in the research on: "{topic}".
        
        Your task is to:
        1. Use the PineconeRetriever tool to search specifically for methodology sections
        2. Compare and contrast different methodological approaches
        3. Evaluate the strengths and limitations of each approach
        4. Identify innovative or novel methodologies
        5. Assess the rigor and validity of the methods used
        
        The output should be a detailed analysis of the methodologies used in the field, 
        their effectiveness, and recommendations for future research.
        """,
        agent=researcher,
        expected_output="A detailed analysis of methodologies with comparisons and evaluations",
        context=[initial_search, identify_themes]
    )
    
    # Task 4: Extract key findings and results
    extract_findings = Task(
        description=f"""
        Extract and synthesize the key findings and results from the research on: "{topic}".
        
        Your task is to:
        1. Use the PineconeRetriever tool to search for results and discussion sections
        2. Identify the major findings across the papers
        3. Note any consistent patterns or trends in the results
        4. Highlight any contradictory findings
        5. Assess the significance and implications of the findings
        
        The output should be a comprehensive synthesis of the key findings in the field, 
        organized thematically and with appropriate context.
        """,
        agent=researcher,
        expected_output="A comprehensive synthesis of key findings organized thematically",
        context=[initial_search, identify_themes, methodology_analysis]
    )
    
    # Task 5: Identify future research directions
    future_directions = Task(
        description=f"""
        Identify future research directions and opportunities related to: "{topic}".
        
        Your task is to:
        1. Use the PineconeRetriever tool to search conclusion sections for future work
        2. Identify gaps and limitations acknowledged by the authors
        3. Note emerging trends or new directions in the field
        4. Suggest potential research questions that remain unanswered
        5. Recommend methodological improvements for future studies
        
        The output should be a forward-looking analysis of where the field is heading, 
        what questions remain unanswered, and what approaches might be fruitful for 
        future research.
        """,
        agent=researcher,
        expected_output="A forward-looking analysis of future research directions and opportunities",
        context=[initial_search, identify_themes, methodology_analysis, extract_findings]
    )
    
    # Return all research tasks
    return [
        initial_search,
        identify_themes,
        methodology_analysis,
        extract_findings,
        future_directions
    ] 