from calendar import c
from crewai import Task, Agent
from typing import List

def create_writing_tasks(writer: Agent) -> List[Task]:
    """Create tasks for the writing phase.
    
    Args:
        writer (Agent): The writer agent
        
    Returns:
        List[Task]: The writing tasks
    """
    
    # Task 1: Create outline
    create_outline = Task(
        description="""
        Create a detailed outline for the review paper based on the research findings.
        
        Your task is to:
        1. Review all the research materials provided by the researcher
        2. Develop a logical structure for the review paper
        3. Create section and subsection headings
        4. Provide brief descriptions of what each section will cover
        5. Ensure the outline follows academic conventions for review papers
        
        The outline should include:
        - Title
        - Abstract
        - Introduction
        - Background/Literature Review
        - Methodology Review
        - Thematic Sections (based on the key themes identified)
        - Discussion of Findings
        - Gaps and Future Directions
        - Conclusion
        - References
        
        The output should be a comprehensive outline that will guide the writing process.
        """,
        agent=writer,
        expected_output="A comprehensive outline with sections, subsections, and brief descriptions",
    )
    
    # Task 2: Write introduction and background
    write_intro = Task(
        description="""
        Write the introduction and background sections of the review paper.
        
        Your task is to:
        1. Craft a compelling introduction that:
           - Introduces the topic and its importance
           - States the purpose and scope of the review
           - Outlines the structure of the paper
           - Provides necessary context for the reader
        
        2. Write a comprehensive background/literature review that:
           - Summarizes the historical development of the field
           - Discusses key theories and concepts
           - Identifies major contributors and their work
           - Sets the stage for the thematic sections
        
        The writing should be scholarly, clear, and engaging, with appropriate citations 
        to the literature. Aim for approximately 1000-1500 words for these sections combined.
        """,
        agent=writer,
        expected_output="Introduction and background sections (1000-1500 words) with appropriate citations",
        context=[create_outline]
    )
    
    # Task 3: Write methodology review
    write_methodology = Task(
        description="""
        Write the methodology review section of the paper.
        
        Your task is to:
        1. Synthesize the methodology analysis provided by the researcher
        2. Compare and contrast different methodological approaches in the field
        3. Discuss the strengths and limitations of various methods
        4. Identify trends in methodological development
        5. Evaluate the rigor and validity of common methods
        
        The writing should be analytical and critical, highlighting methodological 
        innovations as well as persistent challenges. Include appropriate citations 
        and examples from the literature. Aim for approximately 1000-1200 words.
        """,
        agent=writer,
        expected_output="Methodology review section (1000-1200 words) with critical analysis and citations",
        context=[create_outline, write_intro]
    )
    
    # Task 4: Write thematic sections
    write_thematic = Task(
        description="""
        Write the thematic sections of the review paper based on the key themes identified.
        
        Your task is to:
        1. Develop separate sections for each major theme identified in the research
        2. For each theme:
           - Provide a clear introduction to the theme
           - Synthesize relevant findings from multiple papers
           - Highlight agreements and contradictions in the literature
           - Discuss the significance of the theme to the broader topic
           - Include appropriate citations and examples
        
        The writing should be well-structured, with clear transitions between themes 
        and logical flow within each section. Aim for approximately 500-800 words per 
        thematic section, with the number of sections depending on the themes identified.
        """,
        agent=writer,
        expected_output="Thematic sections (500-800 words each) with synthesis of findings and citations",
        context=[create_outline, write_intro, write_methodology]
    )
    
    # Task 5: Write discussion, gaps, and conclusion
    write_conclusion = Task(
        description="""
        Write the discussion, gaps and future directions, and conclusion sections of the review paper.
        
        Your task is to:
        1. Write a discussion section that:
           - Synthesizes the major findings across all themes
           - Identifies patterns, trends, and contradictions
           - Discusses the implications of the findings for theory and practice
        
        2. Write a gaps and future directions section that:
           - Identifies limitations in the current literature
           - Highlights unanswered questions and research gaps
           - Suggests promising directions for future research
           - Recommends methodological improvements
        
        3. Write a conclusion that:
           - Summarizes the key points of the review
           - Reinforces the significance of the topic
           - Offers final thoughts and recommendations
           - Ends with a compelling closing statement
        
        The writing should provide a thoughtful analysis that goes beyond summarizing 
        the literature to offer insights and direction for the field. Aim for approximately 
        1500-2000 words for these sections combined.
        """,
        agent=writer,
        expected_output="Discussion, gaps, and conclusion sections (1500-2000 words) with analysis and recommendations",
        context=[create_outline, write_intro, write_methodology, write_thematic]
    )
    
    # Task 6: Compile references
    compile_references = Task(
        description="""
        Compile a comprehensive list of references for the review paper.
        
        Your task is to:
        1. Gather all citations used throughout the paper
        2. Format the references according to APA style
        3. Ensure all references are complete and accurate
        4. Check for any missing information
        5. Organize the references alphabetically
        
        The output should be a properly formatted reference list that includes all 
        sources cited in the paper, with no omissions or formatting errors.
        """,
        agent=writer,
        expected_output="A comprehensive, properly formatted reference list in APA style",
        context=[write_intro, write_methodology, write_thematic, write_conclusion]
    )
    
    # Task 7: Compile full draft
    compile_draft = Task(
        description="""
        Compile all sections into a complete draft of the review paper.
        
        Your task is to:
        1. Assemble all written sections in the proper order
        2. Ensure consistent formatting throughout the document
        3. Add appropriate transitions between sections
        4. Check that all citations in the text match the reference list
        5. Add a title page with title, authors, and abstract
        
        The output should be a complete, cohesive draft of the review paper that 
        flows logically from beginning to end and adheres to academic conventions.
        """,
        agent=writer,
        expected_output="A complete draft of the review paper with all sections properly assembled",
        context=[create_outline, write_intro, write_methodology, write_thematic, write_conclusion, compile_references]
    )

    Complete_research_review_paper = Task(
        description="""
        Compile all sections into a complete research review paper.
        
        Your task is to:
        0. Based on the research content provided, write a complete review paper that flows logically from beginning to end and adheres to academic conventions that includes Title, Abstract, Introduction, Methods, Main Body(Discussion of Literature),Comparison and Synthesis , Challenges and Limitations, Conclusion and Future Directions , References .
        1. Assemble all written sections in the proper order
        2. Ensure consistent formatting throughout the document
        3. Add appropriate transitions between sections
        4. Check that all citations in the text match the reference list
        Note: Preserve as much information as possible from the provided research content everything should be in the review paper unless irrelevant.
        
        The output should be a complete, cohesive review paper that 
        flows logically from beginning to end and adheres to academic conventions. .
        """,
        agent=writer,
        expected_output="A complete review paper of 3000-6000 words with all sections properly assembled that adheres to academic conventions.",
        context = []
    )
    
    # Return all writing tasks
    # return [
    #     create_outline,
    #     write_intro,
    #     write_methodology,
    #     write_thematic,
    #     write_conclusion,
    #     compile_references,
    #     compile_draft
    # ] 


    return [
        Complete_research_review_paper
    ] 