# 🧠 Elegant Research Assistant

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/streamlit-1.24%2B-red?style=for-the-badge)
![CrewAI](https://img.shields.io/badge/CrewAI-Powered-blue?style=for-the-badge)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT_4-green?style=for-the-badge)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-teal?style=for-the-badge)

An intelligent research assistant that automatically generates comprehensive review papers using multi-agent AI systems.

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [CrewAI System](#-crewai-multi-agent-system) • [Workflow](#-workflow-process) • [Customization](#-customization) • [Sample Interactions](#-sample-interactions)

</div>

---

## 📋 Overview

The Elegant Research Assistant is an advanced AI-powered system that automates the entire process of academic research and review paper generation. Built around the `elegant_research_assistant.py` Streamlit application, it combines:

- 🔍 **Intelligent paper search and retrieval**
- 📊 **Automated PDF processing and analysis**
- 🧮 **Vector embedding and semantic indexing**
- 🤖 **Multi-agent AI collaboration with CrewAI**
- 📝 **Structured review paper generation**
- 🌐 **Interactive Streamlit web interface**

## ✨ Features

- 🔍 **Smart Search**: Advanced research paper discovery across multiple academic sources
- ⬇️ **Intelligent Downloads**: Concurrent paper downloads with smart filtering
- 🤖 **AI-Powered Processing**: Extract and process PDF content with advanced NLP
- 🧠 **Semantic Search**: Vector-based search using Pinecone for accurate results
- 📊 **Session Management**: UUID-based session tracking and retrieval
- 📈 **Progress Tracking**: Real-time download and processing progress monitoring
- 🎯 **Smart Metadata**: Enhanced metadata extraction and processing
- 🖥️ **Modern UI**: Clean and intuitive Streamlit interface
- 📝 **Automated Review Papers**: AI-generated comprehensive research reviews using multi-agent collaboration
- 💡 **Query Suggestions**: AI-powered suggestions to improve your research queries
- 🔄 **Follow-up Questions**: Refine generated reviews with specific follow-up questions
- 🔌 **Limited Mode Operation**: Function without Pinecone for basic review generation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Elegant Research Assistant                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     Streamlit Web Interface                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      Research Pipeline                           │
├─────────────────────┬─────────────────────┬─────────────────────┤
│  Paper Search &     │  PDF Processing     │  Vector Embedding   │
│  Download           │  & Analysis         │  & Indexing         │
└─────────────────────┴─────────────────────┴─────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                    CrewAI Agent System                           │
├─────────────┬─────────────┬─────────────────┬───────────────────┤
│  Manager    │ Researcher  │    Writer       │     Editor        │
│  Agent      │   Agent     │    Agent        │     Agent         │
└─────────────┴─────────────┴─────────────────┴───────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     Generated Review Paper                       │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

<div align="center">
<pre>
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Query    │     │    PDFs     │     │   Chunks    │     │   Vectors   │     │   Review    │
│   Engine    │────▶│  Processor  │────▶│  Generator  │────▶│   Search    │────▶│    Paper    │
│             │     │             │     │             │     │             │     │  Generator  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   ▲                   │                   │                   │
      │                   │                   │                   │                   │
      ▼                   │                   ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Academic   │     │   Paper     │     │  OpenAI     │     │  Pinecone   │     │   CrewAI    │
│  Sources    │     │ Repository  │     │ Embeddings  │     │   Vector    │     │  Agents &   │
│             │     │             │     │             │     │    DB       │     │   Tasks     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
</pre>
</div>

## 🚀 Installation

### Prerequisites
- Python 3.9+
- OpenAI API key
- Pinecone API key

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/elegant-research-assistant.git
cd elegant-research-assistant
```

2. **Set up virtual environment**
```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Unix/MacOS
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the project root:
```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional API Keys
GEMINI_API_KEY=your_gemini_api_key  # For query suggestions

# Pinecone Configuration
PINECONE_INDEX_NAME=deepresearchreviewbot  # Default index name
```

## 📖 Usage

### Streamlit Web Interface

The main entry point for the application is `elegant_research_assistant.py`, which provides a user-friendly Streamlit interface for all functionality.

```bash
# Activate the virtual environment (if not already activated)
# Windows
.\venv\Scripts\Activate.ps1

# Launch the application
streamlit run elegant_research_assistant.py
```

### Using the Interface

1. **Enter a research query** in the main input field
2. **Choose an action**:
   - **Write Research Review**: Process the query and generate a complete review paper
   - **Process Query Only**: Download and process papers without generating a review
3. **Track progress** in the sidebar status section
4. **View and download** the generated review paper
5. **Ask follow-up questions** to refine the review

### Real-time Progress Tracking

The application provides real-time progress updates through:
- Status indicators in the sidebar
- Progress bars for each processing stage
- Live output from the CrewAI agents during review generation

### Session Management

- Each research session is assigned a unique UUID
- You can retrieve previous sessions by entering the UUID in the sidebar
- Session data is stored in the `downloads/{UUID}` directory
- The sidebar "Quick Actions" section allows generating review papers from existing sessions

## 🤖 CrewAI Multi-Agent System

The heart of the review paper generation process is a specialized CrewAI multi-agent system integrated directly into the Streamlit application. The system works collaboratively through:

### 👨‍💼 Manager Agent
- Oversees the entire review paper generation process
- Coordinates between other agents
- Ensures coherent integration of all components
- Maintains focus on the research topic

### 🔍 Researcher Agent
- Utilizes semantic search to find relevant research chunks
- Filters results by relevance scores
- Works with document chunks and their positions
- Manages citations and analyzes content across multiple documents
- Uses the PineconeRetriever tool to access the vector database

### ✍️ Writer Agent
- Drafts comprehensive, well-structured review papers
- Synthesizes information from multiple document sections
- Properly attributes sources using citation information
- Creates coherent narratives from research content
- Follows academic writing conventions and standards

### 📝 Editor Agent
- Reviews and refines the draft review paper
- Ensures logical flow and coherence
- Checks citation formatting and consistency
- Improves clarity and readability
- Ensures academic standards are maintained

### Agent Interaction Visualization

```
Manager Agent
    │
    ├── Assigns tasks to ──► Researcher Agent ──► PineconeRetriever Tool
    │                             │
    │                             ▼
    │                       Research Findings
    │                             │
    ├── Coordinates with ───► Writer Agent
    │                             │
    │                             ▼
    │                        Draft Paper
    │                             │
    └── Reviews with ────────► Editor Agent
                                  │
                                  ▼
                           Final Review Paper
```

## 🔄 Workflow Process

<div align="center">
  <table>
    <tr>
      <td align="center"><b>Step 1</b></td>
      <td align="center"><b>Step 2</b></td>
      <td align="center"><b>Step 3</b></td>
      <td align="center"><b>Step 4</b></td>
      <td align="center"><b>Step 5</b></td>
    </tr>
    <tr>
      <td align="center">🔍</td>
      <td align="center">📄</td>
      <td align="center">🔢</td>
      <td align="center">🧠</td>
      <td align="center">🤖</td>
    </tr>
    <tr>
      <td align="center">Paper Discovery</td>
      <td align="center">PDF Processing</td>
      <td align="center">Vector Indexing</td>
      <td align="center">Semantic Search</td>
      <td align="center">Review Generation</td>
    </tr>
  </table>
</div>

1. **Query Processing**: User enters a research topic
2. **Paper Retrieval**: System searches and downloads relevant academic papers
3. **PDF Processing**: Papers are processed, text extracted, and metadata captured
4. **Vector Indexing**: Document chunks are embedded and indexed in Pinecone
5. **CrewAI Activation**: Multi-agent system is initialized with the research topic
6. **Research Phase**: Researcher agent retrieves and analyzes relevant content
7. **Writing Phase**: Writer agent drafts a comprehensive review paper
8. **Editing Phase**: Editor agent refines and improves the draft
9. **Final Output**: Completed review paper is presented to the user

## 🛠️ Tools and Technologies

### Vector Database
- **Pinecone**: Stores and retrieves document embeddings for semantic search

### Retrieval Tools
- **PineconeRetriever**: Custom CrewAI tool for semantic search in the vector database
- **Citation Manager**: Manages and formats academic citations

### Language Models
- **GPT-4o**: Powers the Writer Agent for high-quality content generation
- **GPT-4o-mini**: Powers the Researcher Agent for efficient information retrieval
- **Embedding Models**: OpenAI's text-embedding-3-large for document vectorization

### Frontend
- **Streamlit**: Interactive web interface with real-time progress updates
- **Custom StreamToExpander**: Real-time output display in the Streamlit interface

## 📄 Example Output

The system generates well-structured review papers in Markdown format, including:

- Title and introduction
- Background and theoretical foundations
- Methodology overview
- Key findings and analysis
- Discussion of implications
- Conclusion and future directions
- Properly formatted references

## 🔬 Sample Interactions

Explore real-world examples of the Elegant Research Assistant in action by visiting our [Sample Interactions](https://www.linkedin.com/in/umagunda/overlay/experience/2118644624/multiple-media-viewer/?profileId=ACoAADJQQpIBQlVsXCZOANyZoVFiOGlxCZXQJQQ&treasuryMediaId=1635542875242) folder. This collection includes:

- Generated review papers on various topics
- Examples of different research depths and complexities
- Demonstrations of the system's capabilities for different academic domains

These samples showcase how the assistant handles diverse research queries and generates comprehensive review papers with proper citations and academic structure.

## 🔧 Customization

You can customize the review paper generation by modifying:
- The agent prompts in `review_paper_writing_crew_new/agents/`
- The task definitions in `review_paper_writing_crew_new/tasks/`
- The retrieval parameters in `review_paper_writing_crew_new/tools/retriever.py`

## 📚 Project Structure

```
elegant-research-assistant/
├── 📜 elegant_research_assistant.py  # Main application entry point with Streamlit UI
├── 📂 research_paper_downloader/     # Paper downloading module
├── 📄 pdf_processor_pymupdf.py       # PDF processing module
├── 📋 requirements.txt               # Project dependencies
├── 🔑 .env                           # Environment variables (not in git)
├── 📂 review_paper_writing_crew_new/ # AI-powered research paper writing module
│   ├── 📜 main.py                    # Entry point for the review paper generation
│   ├── 📂 agents/                    # CrewAI agent definitions
│   │   ├── 📄 manager_agent.py       # Oversees the entire paper generation process
│   │   ├── 📄 researcher_agent.py    # Retrieves and analyzes research papers
│   │   ├── 📄 writer_agent.py        # Drafts sections of the review paper
│   │   └── 📄 editor_agent.py        # Refines and polishes the final paper
│   ├── 📂 tasks/                     # Task definitions for each agent
│   │   ├── 📄 research_tasks.py      # Tasks for literature search and analysis
│   │   ├── 📄 writing_tasks.py       # Tasks for drafting paper sections
│   │   └── 📄 editing_tasks.py       # Tasks for editing and refinement
│   ├── 📂 tools/                     # Custom tools for agents
│   │   ├── 📄 retriever.py           # Pinecone vector search tool
│   │   └── 📄 citation_manager.py    # Manages paper citations
│   └── 📂 utils/                     # Utility functions
└── 📁 downloads/                     # Downloaded papers and processed data
    └── {session-uuid}/
        ├── 📚 papers/                # Downloaded PDF files
        ├── 🔍 processed_data/        # Processed paper data
        └── 📝 *_review.md            # Generated review papers
```

## 🔧 Troubleshooting

### Environment Variable Issues

If you encounter issues related to environment variables, try these solutions:

1. **API Key Not Found**
   ```
   Error: OPENAI_API_KEY/PINECONE_API_KEY not found
   ```
   - Ensure your `.env` file is in the correct location (project root)
   - Check that the variable names match exactly (case-sensitive)
   - Verify there are no spaces around the equals sign: `KEY=value` (not `KEY = value`)

2. **Module Can't Find Environment Variables**
   - Create a module-specific `.env` file in the module directory
   - Or use absolute paths in your code:
     ```python
     from dotenv import load_dotenv
     import os
     
     # Load from project root
     load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
     ```

3. **Invalid API Keys**
   - Verify your API keys are valid and active
   - Check for any whitespace or special characters that might have been copied

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [CrewAI](https://github.com/joaomdmoura/crewAI) for the multi-agent framework
- [Streamlit](https://streamlit.io/) for the web interface
- [Pinecone](https://www.pinecone.io/) for vector database capabilities
- [OpenAI](https://openai.com/) for language models
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing

---

<div align="center">

Made with ❤️ by Uma Maheshwar Gupta Gunda

</div> 