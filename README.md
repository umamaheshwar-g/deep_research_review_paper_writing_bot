# 🧠 Elegant Research Assistant

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![CrewAI](https://img.shields.io/badge/CrewAI-Powered-blue?style=for-the-badge)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT_4-green?style=for-the-badge)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-teal?style=for-the-badge)

</div>

## 📋 Overview

Elegant Research Assistant automates the process of academic research paper generation using multi-agent AI systems. It searches, downloads, and analyzes academic papers to create comprehensive review papers with proper citations and academic structure.

## ✨ Key Features

- 🔍 **Intelligent Paper Search**: Discovers relevant academic papers across multiple sources
- 📝 **Automated Review Papers**: Generates comprehensive research reviews using AI agents
- 🧠 **Semantic Search**: Performs vector-based search for accurate information retrieval
- 📊 **Real-time Progress Tracking**: Monitors paper discovery, downloads, and processing
- 💡 **Interactive Refinement**: Allows follow-up questions to refine generated reviews

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           ELEGANT RESEARCH ASSISTANT                                           │
└───────────────────────────────────────────────┬───────────────────────────────────────────────────────────────┘
                                                │
                ┌───────────────────────────────▼───────────────────────────────┐
                │                    STREAMLIT WEB INTERFACE                     │
                │                                                                │
                │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
                │  │  Query Input   │  │Progress Tracking│  │ Results Display│   │
                │  └────────────────┘  └────────────────┘  └────────────────┘   │
                └───────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         RESEARCH PAPER PIPELINE                                                │
│                                                                                                               │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────────┐    ┌──────────────────────────┐  │
│  │      PAPER DISCOVERY SYSTEM     │    │       PDF PROCESSING SYSTEM      │    │   VECTOR INDEXING SYSTEM │  │
│  │                                 │    │                                  │    │                          │  │
│  │  ┌─────────────┐ ┌────────────┐│    │  ┌─────────────┐ ┌─────────────┐ │    │  ┌─────────────────────┐ │  │
│  │  │Query Module │ │API Clients ││    │  │PDF Extractor│ │Text Chunking│ │    │  │OpenAI Embedding API│ │  │
│  │  └─────────────┘ └────────────┘│    │  └─────────────┘ └─────────────┘ │    │  └─────────────────────┘ │  │
│  │                                 │    │                                  │    │             │            │  │
│  │  ┌─────────────────────────────┤    │  ┌─────────────┐ ┌─────────────┐ │    │             ▼            │  │
│  │  │   ACADEMIC SOURCES          │    │  │ Structure   │ │Metadata     │ │    │  ┌─────────────────────┐ │  │
│  │  │                             │    │  │ Analysis    │ │Extraction   │ │    │  │   PINECONE DB       │ │  │
│  │  │ ┌─────────┐  ┌────────────┐ │    │  └─────────────┘ └─────────────┘ │    │  │                     │ │  │
│  │  │ │ CrossRef│  │PubMed      │ │    │                                  │    │  │  ┌───────────────┐  │ │  │
│  │  │ └─────────┘  └────────────┘ │    │  ┌─────────────────────────────┐ │    │  │  │ Vector Index  │  │ │  │
│  │  │                             │    │  │      CITATION MANAGER        │ │    │  │  └───────────────┘  │ │  │
│  │  │ ┌─────────┐  ┌────────────┐ │    │  │                             │ │    │  │                     │ │  │
│  │  │ │Semantic │  │Google      │ │    │  │  ┌───────────┐ ┌──────────┐ │ │    │  │  ┌───────────────┐  │ │  │
│  │  │ │Scholar  │  │Scholar     │ │    │  │  │Reference  │ │APA Format│ │ │    │  │  │Namespace Mgmt │  │ │  │
│  │  │ └─────────┘  └────────────┘ │    │  │  │Extraction │ │Generator │ │ │    │  │  └───────────────┘  │ │  │
│  │  └─────────────────────────────┘    │  │  └───────────┘ └──────────┘ │ │    │  │                     │ │  │
│  │                                     │  └─────────────────────────────┘ │    │  └─────────────────────┘ │  │
│  └─────────────────────────────────────┘    └──────────────────────────────┘    └──────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        CREWAI MULTI-AGENT SYSTEM                                               │
│                                                                                                               │
│  ┌─────────────────────────────────────┐                          ┌─────────────────────────────────────────┐ │
│  │         RESEARCHER AGENT            │                          │             WRITER AGENT                 │ │
│  │                                     │                          │                                         │ │
│  │  ┌───────────────────────────────┐  │                          │  ┌─────────────────────────────────┐   │ │
│  │  │     RESEARCH TASKS            │  │                          │  │          WRITING TASK           │   │ │
│  │  │                               │  │                          │  │                                 │   │ │
│  │  │ 1. Initial Literature Search  │  │                          │  │ Complete Research Review Paper  │   │ │
│  │  │ 2. Background & Theory        │  │                          │  │   - Title & Abstract            │   │ │
│  │  │ 3. Key Themes Identification  │  │                          │  │   - Introduction                │   │ │
│  │  │ 4. Taxonomy Development       │  │───┐                      │  │   - Methods Analysis            │   │ │
│  │  │ 5. Methodology Analysis       │  │   │                      │  │   - Thematic Sections           │   │ │
│  │  │ 6. Extract & Synthesize       │  │   │                      │  │   - Synthesis & Comparison      │   │ │
│  │  │ 7. Challenges & Open Issues   │  │   │                      │  │   - Challenges & Limitations    │   │ │
│  │  │ 8. Future Directions          │  │   │                      │  │   - Conclusion                  │   │ │
│  │  │ 9. Conclusion & Summary       │  │   │                      │  │   - References                  │   │ │
│  │  └───────────────────────────────┘  │   │                      │  └─────────────────────────────────┘   │ │
│  │                │                     │   │                      │                  │                     │ │
│  │                ▼                     │   │                      │                  │                     │ │
│  │  ┌───────────────────────────────┐  │   │                      │                  │                     │ │
│  │  │      RETRIEVER TOOL           │  │   │                      │                  │                     │ │
│  │  │                               │  │   │                      │                  │                     │ │
│  │  │ ┌─────────────────────────┐   │  │   │                      │                  │                     │ │
│  │  │ │  PineconeRetriever      │   │  │   │                      │                  │                     │ │
│  │  │ │                         │◄──┼──┼───┼──────────────────────┼─────────────────┘                     │ │
│  │  │ │  - Document Access      │   │  │   │                      │                                       │ │
│  │  │ │  - Vector Search        │   │  │   │                      │                                       │ │
│  │  │ │  - Relevance Filtering  │   │  │   │                      │                                       │ │
│  │  │ └─────────────────────────┘   │  │   │                      │                                       │ │
│  │  └───────────────────────────────┘  │   │                      └─────────────────────────────────────────┘ │
│  └─────────────────────────────────────┘   │                                                                  │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         OUTPUT GENERATION                                                      │
│                                                                                                               │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────────┐    ┌──────────────────────────┐  │
│  │      MARKDOWN FORMATTING        │    │       CITATION FORMATTING        │    │  USER PRESENTATION       │  │
│  │                                 │    │                                  │    │                          │  │
│  │  - Academic Structure           │    │  - APA Style References          │    │  - Streamlit Display     │  │
│  │  - Section Organization         │    │  - In-text Citations             │    │  - Download Options      │  │
│  │  - Heading Hierarchy            │    │  - Bibliography Generation        │    │  - Follow-up Interface   │  │
│  └─────────────────────────────────┘    └─────────────────────────────────┘    └──────────────────────────┘  │
│                                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 🌐 Academic Sources

The system draws research papers from multiple academic sources:

- **CrossRef**: Comprehensive database of scholarly publications with DOI references
- **PubMed**: Leading source for biomedical and life science research
- **Semantic Scholar**: AI-powered research tool with enhanced semantic understanding
- **Google Scholar**: Wide-ranging academic search engine covering various disciplines

Papers are retrieved using specialized API interactions and smart downloader tools that:
1. Fetch metadata from academic databases
2. Evaluate papers' relevance to the research topic
3. Download full-text PDFs using DOI resolution and direct access methods
4. Extract text and structure for comprehensive analysis

This multi-source approach ensures broad coverage across research domains and maximizes access to relevant literature.

## 🤖 CrewAI Multi-Agent System

The system employs a focused CrewAI framework with two specialized agents working sequentially:

1. **Researcher Agent** - Equipped with a PineconeRetriever tool to:
   - Conduct initial literature search (20-30 key papers)
   - Analyze theoretical foundations and background
   - Identify key themes and research questions
   - Develop taxonomy and classification systems
   - Analyze research methodologies across papers
   - Extract and synthesize key findings
   - Identify challenges and open research issues
   - Map future research directions
   - Prepare conclusion and summary insights

2. **Writer Agent** - Creates the final review paper by:
   - Compiling all research findings into a comprehensive academic review
   - Structuring the paper with proper academic sections
   - Creating a cohesive narrative across multiple research themes
   - Ensuring proper citations and references
   - Maintaining scholarly language and style

The system follows a sequential process model, where research tasks are completed before writing begins, ensuring comprehensive analysis before synthesis.

### Task Workflow

```
Researcher Agent Tasks
    │
    ├── Initial Literature Search ──────────────────┐
    │                                              │
    ├── Background & Theoretical Foundations        │
    │                                              │
    ├── Identify Key Themes                         │
    │                                              │
    ├── Develop Taxonomy                            │
    │                                              ▼
    ├── Analyze Methodologies             PineconeRetriever Tool
    │                                     (Semantic Vector Search)
    ├── Extract & Synthesize Findings
    │
    ├── Identify Challenges & Open Issues
    │
    ├── Map Future Research Directions
    │
    └── Conclude & Summarize
           │
           ▼
Writer Agent Task
    │
    └── Complete Research Review Paper
```

## 🔄 Workflow Process

1. **Research Topic Input**: User enters a research topic via the Streamlit interface
2. **Document Processing**: System processes previously downloaded and indexed papers
3. **Research Phase**: Researcher agent executes 9 sequential tasks to analyze the literature
   - Each task builds context from previous tasks
   - The PineconeRetriever tool accesses relevant document chunks
  │   Local document IDs are tracked to maintain paper references

4. **Writing Phase**: Writer agent compiles findings into a complete review paper with:
   - Title and abstract
   - Introduction and background
   - Methods analysis
   - Main thematic sections
   - Comparative synthesis
   - Challenges and limitations
   - Conclusion and future directions
   - Properly formatted references

5. **Output Generation**: Final paper is formatted as markdown and presented to the user

## 🚀 Installation & Usage

### Prerequisites
- Python 3.9+
- OpenAI API key
- Pinecone API key

### Quick Start

1. **Clone the repository and install dependencies**
```bash
git clone https://github.com/yourusername/elegant-research-assistant.git
cd elegant-research-assistant
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **Set up API keys in .env file**
```env
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

3. **Run the application**
```bash
streamlit run elegant_research_assistant.py
```

## 🛠️ Technologies Used

- **CrewAI**: Multi-agent framework for collaborative AI
- **OpenAI GPT-4**: Powers the Writer Agent
- **Pinecone**: Vector database for semantic search
- **Streamlit**: Interactive web interface
- **PyMuPDF**: PDF processing and text extraction

## 📚 Project Structure

```
elegant-research-assistant/
├── 📜 elegant_research_assistant.py  # Main application with Streamlit UI
├── 📂 research_paper_downloader/     # Paper downloading module
├── 📄 pdf_processor_pymupdf.py       # PDF processing module
├── 📂 review_paper_writing_crew_new/ # AI-powered research paper writing module
│   ├── 📂 agents/                    # CrewAI agent definitions
│   ├── 📂 tasks/                     # Task definitions for agents
│   └── 📂 tools/                     # Custom tools for agents
└── 📁 downloads/                     # Downloaded papers and generated reviews
```

## 📄 Example Output

The system generates well-structured review papers in Markdown format, including:

- Title and introduction
- Background and theoretical foundations
- Key findings and analysis
- Discussion and implications
- Conclusion and future directions
- Properly formatted references

---

<div align="center">
Made with ❤️ by Uma Maheshwar Gupta Gunda
</div> 