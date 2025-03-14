# Deep Research Review Paper Writing Crew - Project Summary

## Overview

This project implements a multi-agent system using CrewAI to automatically generate research review papers based on academic papers stored in a Pinecone vector database. The system uses a team of specialized AI agents that work together to research, write, and edit comprehensive review papers on any given topic.

## Key Components

### Agents

1. **Manager Agent** (`agents/manager_agent.py`)
   - Coordinates the overall review paper writing process
   - Oversees the work of other agents
   - Ensures the final paper meets academic standards

2. **Researcher Agent** (`agents/researcher_agent.py`)
   - Retrieves relevant papers from the Pinecone vector database
   - Analyzes and synthesizes information from multiple papers
   - Identifies key themes, methodologies, findings, and future directions

3. **Writer Agent** (`agents/writer_agent.py`)
   - Creates a structured outline for the review paper
   - Writes the various sections of the paper
   - Ensures proper citation and formatting

4. **Editor Agent** (`agents/editor_agent.py`)
   - Reviews the paper for content quality and structural coherence
   - Checks for academic rigor and scholarly standards
   - Polishes language, style, and citations

### Tools

1. **Pinecone Retriever** (`tools/retriever.py`)
   - Connects to the Pinecone vector database
   - Performs semantic searches to find relevant papers
   - Supports various filtering options (page numbers, scores, etc.)

2. **Citation Manager** (`tools/citation_manager.py`)
   - Manages citations for the review paper
   - Formats citations according to academic standards (APA)
   - Maintains a database of cited papers

### Tasks

1. **Research Tasks** (`tasks/research_tasks.py`)
   - Initial literature search
   - Identification of key themes and concepts
   - Analysis of methodologies
   - Extraction of key findings
   - Identification of future research directions

2. **Writing Tasks** (`tasks/writing_tasks.py`)
   - Creating a detailed outline
   - Writing introduction and background
   - Writing methodology review
   - Writing thematic sections
   - Writing discussion, gaps, and conclusion
   - Compiling references
   - Assembling the full draft

3. **Editing Tasks** (`tasks/editing_tasks.py`)
   - Reviewing content and structure
   - Checking academic rigor
   - Polishing language and style
   - Verifying citations and references
   - Final revision and polishing

## How It Works

1. The user specifies a research topic and optional parameters
2. The system generates a unique namespace for the Pinecone database
3. The manager agent coordinates the work of the other agents
4. The researcher agent retrieves and analyzes relevant papers
5. The writer agent creates a structured review paper
6. The editor agent reviews and refines the paper
7. The final paper is saved to the specified output file

## Usage

```bash
python main.py --topic "Your research topic" --output "output_filename.md"
```

Or use the example script:

```bash
python run_example.py --topic "Diffusion Large Language Models"
```

## Future Enhancements

1. Add support for multiple citation styles
2. Implement a feedback loop for iterative improvement
3. Add visualization tools for research findings
4. Integrate with academic databases beyond Pinecone
5. Add support for collaborative writing with human input 