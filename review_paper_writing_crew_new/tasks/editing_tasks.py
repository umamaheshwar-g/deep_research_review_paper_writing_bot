from crewai import Task, Agent
from typing import List

def create_editing_tasks(editor: Agent) -> List[Task]:
    """Create tasks for the editing phase.
    
    Args:
        editor (Agent): The editor agent
        
    Returns:
        List[Task]: The editing tasks
    """
    
    # Task 1: Review for content and structure
    content_review = Task(
        description="""
        Review the draft paper for content quality and structural coherence.
        
        Your task is to:
        1. Evaluate the overall organization and flow of the paper
        2. Assess whether the content adequately covers the topic
        3. Check for logical progression of ideas
        4. Identify any gaps or redundancies in the content
        5. Evaluate the balance between different sections
        
        Provide specific feedback on:
        - The strength of the introduction and conclusion
        - The coherence of the thematic sections
        - The quality of synthesis and analysis
        - The clarity of the methodology review
        - The thoroughness of the gaps and future directions section
        
        The output should be a detailed review with specific recommendations for 
        improving the content and structure of the paper.
        """,
        agent=editor,
        expected_output="A detailed review of content and structure with specific recommendations",
    )
    
    # Task 2: Review for academic rigor
    academic_review = Task(
        description="""
        Review the draft paper for academic rigor and scholarly standards.
        
        Your task is to:
        1. Evaluate the quality and appropriateness of citations
        2. Check for proper attribution of ideas
        3. Assess the depth of analysis and critical thinking
        4. Verify that claims are supported by evidence
        5. Ensure that different perspectives are fairly represented
        
        Provide specific feedback on:
        - The use of primary vs. secondary sources
        - The currency and relevance of cited works
        - The balance between description and analysis
        - The handling of contradictory findings
        - The scholarly tone and language
        
        The output should be a detailed review with specific recommendations for 
        enhancing the academic rigor of the paper.
        """,
        agent=editor,
        expected_output="A detailed review of academic rigor with specific recommendations",
        context=[content_review]
    )
    
    # Task 3: Review for language and style
    language_review = Task(
        description="""
        Review the draft paper for language quality, style, and clarity.
        
        Your task is to:
        1. Identify any issues with grammar, syntax, or punctuation
        2. Check for consistency in terminology and style
        3. Evaluate the clarity and precision of language
        4. Assess the readability and flow of sentences and paragraphs
        5. Check for appropriate academic tone
        
        Provide specific feedback on:
        - Sentence structure and variety
        - Paragraph organization and transitions
        - Word choice and terminology
        - Active vs. passive voice usage
        - Conciseness and precision
        
        The output should be a detailed review with specific recommendations for 
        improving the language and style of the paper.
        """,
        agent=editor,
        expected_output="A detailed review of language and style with specific recommendations",
        context=[content_review, academic_review]
    )
    
    # Task 4: Review citations and references
    citation_review = Task(
        description="""
        Review the citations and references in the draft paper.
        
        Your task is to:
        1. Check that all in-text citations have corresponding entries in the reference list
        2. Verify that all entries in the reference list are cited in the text
        3. Ensure that citations and references follow APA style consistently
        4. Check for any missing information in the references
        5. Verify the formatting of different types of sources (journals, books, etc.)
        
        Provide specific feedback on:
        - Any missing citations or references
        - Any formatting inconsistencies
        - Any incomplete reference entries
        - The overall organization of the reference list
        - The balance and variety of sources
        
        The output should be a detailed review with specific recommendations for 
        correcting and improving the citations and references.
        """,
        agent=editor,
        expected_output="A detailed review of citations and references with specific recommendations",
        context=[content_review, academic_review, language_review]
    )
    
    # Task 5: Final revision and polishing
    final_revision = Task(
        description="""
        Perform a final revision and polishing of the review paper.
        
        Your task is to:
        1. Incorporate all the feedback from previous review tasks
        2. Make necessary revisions to improve content, structure, language, and citations
        3. Ensure consistency throughout the paper
        4. Polish the writing for clarity, precision, and impact
        5. Perform a final check for any remaining issues
        
        The output should be a polished, publication-ready version of the review paper 
        that meets high academic standards in terms of content, structure, language, 
        and formatting.
        """,
        agent=editor,
        expected_output="A polished, publication-ready version of the review paper",
        context=[content_review, academic_review, language_review, citation_review]
    )
    
    # Return all editing tasks
    return [
        content_review,
        academic_review,
        language_review,
        citation_review,
        final_revision
    ] 