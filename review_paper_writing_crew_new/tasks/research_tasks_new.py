from crewai import Task, Agent
from typing import List

def create_research_tasks(topic: str, researcher: Agent) -> List[Task]:
    """Creates a structured set of research tasks for conducting a comprehensive review.
    
    Args:
        topic (str): The research topic.
        researcher (Agent): The researcher agent responsible for executing tasks.
    
    Returns:
        List[Task]: A list of well-defined research tasks.
    """
    
    # Task 1: Conduct an Initial Literature Search
    initial_search = Task(
        description=f"""
        Perform an initial literature search on the topic: "{topic}".
        
        Responsibilities:
        - Utilize the PineconeRetriever tool to find the most relevant papers.
        - Identify and curate a list of 20-30 key papers along with local ids, essential to the review.
        - Extract and document metadata  along with data chunks and summaries.
        - Organize chunks based on relevance and impact on the topic.
        - Provide a structured report of findings, including justifications for each paper's inclusion.
        - keep track of local_ids/paper_id for filtering and deep research
        """,
        agent=researcher,
        expected_output="A structured list of 20-30 key papers with metadata and relevance assessment."
    )
    
    # Task 2: Provide Background and Theoretical Foundations
    background_section = Task(
        description=f"""
        Develop a background section outlining the theoretical foundations of: "{topic}".
        
        Responsibilities:
        - Summarize fundamental concepts and historical developments.
        - Explain key terminologies and definitions.
        - Provide an overview of significant milestones in the field.
        - Introduce any relevant frameworks or models.
        - keep track of local_ids/paper_id for filtering and deep research

        """,
        agent=researcher,
        expected_output="A well-structured background section covering theoretical foundations and key concepts.",
        context=[initial_search]
    )
    
    # Task 3: Identify Key Themes and Research Questions
    identify_themes = Task(
        description=f"""
        Analyze the key themes, concepts, and research questions from the selected papers on: "{topic}".
        
        Responsibilities:
        - Extract major themes and recurring concepts from the literature.
        - Identify commonly used methodologies and their significance.
        - Highlight debates, contradictions, and unresolved issues.
        - Detect gaps in current research.
        - Propose a conceptual framework to structure the review.
        - keep track of local_ids/paper_id for filtering and deep research

        """,
        agent=researcher,
        expected_output="A comprehensive thematic analysis including methodologies, debates, and research gaps.",
        context=[initial_search, background_section]
    )
    
    # Task 4: Develop a Taxonomy or Classification
    taxonomy_section = Task(
        description=f"""
        Create a taxonomy or classification system for organizing research in the field of: "{topic}".
        
        Responsibilities:
        - Identify key categories and subcategories in the literature.
        - Group related research based on methodologies, applications, or theoretical perspectives.
        - Provide a clear and logical classification framework.
        - Justify the categorization with supporting literature.
        - keep track of local_ids/paper_id for filtering and deep research

        """,
        agent=researcher,
        expected_output="A structured taxonomy with categories and justifications.",
        context=[identify_themes]
    )
    
    # Task 5: Analyze Research Methodologies
    methodology_analysis = Task(
        description=f"""
        Conduct an in-depth analysis of research methodologies used in studies on: "{topic}".
        
        Responsibilities:
        - Retrieve methodology sections from relevant papers.
        - Compare and contrast different research approaches.
        - Evaluate strengths, limitations, and innovations in methodologies.
        - Assess the rigor, validity, and reliability of applied methods.
        - Identify trends in methodological advancements.
        - keep track of local_ids/paper_id for filtering and deep research
        """,
        agent=researcher,
        expected_output="A detailed methodological review with comparisons and evaluations.",
        context=[initial_search, identify_themes]
    )
    
    # Task 6: Extract and Synthesize Key Findings
    extract_findings = Task(
        description=f"""
        Synthesize key findings and results from existing research on: "{topic}".
        
        Responsibilities:
        - Extract major results from the selected papers.
        - Identify consistent patterns, trends, and significant discoveries.
        - Highlight conflicting findings and discuss possible explanations.
        - Assess the broader impact and implications of these results.
        - Organize findings into a coherent thematic synthesis.
        - keep track of local_ids/paper_id for filtering and deep research
        """,
        agent=researcher,
        expected_output="A synthesized report of key findings organized thematically with contextual analysis.",
        context=[initial_search, identify_themes, methodology_analysis]
    )
    
    # Task 7: Identify Challenges and Open Issues
    challenges_section = Task(
        description=f"""
        Identify current challenges and open research issues related to: "{topic}".
        
        Responsibilities:
        - Summarize challenges and limitations identified in the literature.
        - Highlight unresolved issues and research bottlenecks.
        - Discuss potential solutions proposed in previous studies.
        - Provide a critical evaluation of ongoing debates and challenges.
        - keep track of local_ids/paper_id for filtering and deep research
        """,
        agent=researcher,
        expected_output="A detailed discussion on challenges, open issues, and potential solutions.",
        context=[extract_findings]
    )
    
    # Task 8: Identify Future Research Directions
    future_directions = Task(
        description=f"""
        Identify gaps, limitations, and opportunities for future research on: "{topic}".
        
        Responsibilities:
        - Examine conclusion sections for proposed future work.
        - Identify emerging research trends and unexplored areas.
        - Suggest new research questions and hypotheses.
        - Recommend methodological improvements for advancing the field.
        - Provide a forward-looking analysis to guide future studies.
        - keep track of local_ids/paper_id for filtering and deep research
        """,
        agent=researcher,
        expected_output="A well-reasoned discussion on future research directions and emerging trends.",
        context=[challenges_section]
    )
    
    # Task 9: Conclusion and Summary
    conclusion_section = Task(
        description=f"""
        Summarize the key insights, contributions, and conclusions from the review on: "{topic}".
        
        Responsibilities:
        - Provide a concise summary of key findings.
        - Highlight the main contributions of the review.
        - Offer final thoughts on the state of the field.
        - Emphasize the importance of addressing identified gaps.
        - keep track of local_ids/paper_id for filtering and deep research
        """,
        agent=researcher,
        expected_output="A well-structured conclusion summarizing the review's contributions and insights.",
        context=[future_directions]
    )
    
    # Return all research tasks
    return [
        initial_search,
        background_section,
        identify_themes,
        taxonomy_section,
        methodology_analysis,
        extract_findings,
        challenges_section,
        future_directions,
        conclusion_section
    ]
