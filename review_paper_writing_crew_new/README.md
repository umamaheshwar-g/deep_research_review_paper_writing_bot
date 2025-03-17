# 🧠 Elegant Research Assistant

<div align="center">
  <img src="https://img.shields.io/badge/CrewAI-Powered-blue?style=for-the-badge" alt="CrewAI Powered"/>
  <img src="https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=for-the-badge" alt="Streamlit Frontend"/>
  <img src="https://img.shields.io/badge/Pinecone-Vector_DB-teal?style=for-the-badge" alt="Pinecone Vector DB"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT_4-green?style=for-the-badge" alt="OpenAI GPT-4"/>
</div>

<p align="center">
  <i>An intelligent research assistant that automatically generates comprehensive review papers using multi-agent AI systems</i>
</p>

## 📋 Overview

The Elegant Research Assistant is an advanced AI-powered system that automates the entire process of academic research and review paper generation. It combines:

- 🔍 **Intelligent paper search and retrieval**
- 📊 **Automated PDF processing and analysis**
- 🧮 **Vector embedding and semantic indexing**
- 🤖 **Multi-agent AI collaboration with CrewAI**
- 📝 **Structured review paper generation**
- 🌐 **Interactive Streamlit web interface**

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

## 🤖 CrewAI Multi-Agent System

The heart of the review paper generation process is a specialized CrewAI multi-agent system that works collaboratively:

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

## 🔄 Workflow Process

1. **Query Processing**: User enters a research topic
2. **Paper Retrieval**: System searches and downloads relevant academic papers
3. **PDF Processing**: Papers are processed, text extracted, and metadata captured
4. **Vector Indexing**: Document chunks are embedded and indexed in Pinecone
5. **CrewAI Activation**: Multi-agent system is initialized with the research topic
6. **Research Phase**: Researcher agent retrieves and analyzes relevant content
7. **Writing Phase**: Writer agent drafts a comprehensive review paper
8. **Editing Phase**: Editor agent refines and improves the draft
9. **Final Output**: Completed review paper is presented to the user

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- OpenAI API key
- Pinecone API key

### Installation

1. Clone this repository
```bash
git clone https://github.com/yourusername/elegant-research-assistant.git
cd elegant-research-assistant
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys
```
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
GEMINI_API_KEY=your_gemini_api_key  # Optional
```

### Running the Application

Launch the Streamlit interface:
```bash
streamlit run elegant_research_assistant.py
```

## 📊 Features

- **Intelligent Query Suggestions**: Get AI-powered suggestions to improve your research queries
- **Session Management**: Save and retrieve research sessions with unique IDs
- **Real-time Progress Updates**: Monitor the progress of each step in the research process
- **Interactive Review Paper Generation**: Generate comprehensive review papers with a single click
- **Follow-up Questions**: Refine generated reviews with specific follow-up questions
- **Limited Mode Operation**: Function without Pinecone for basic review generation

## 📄 Example Output

The system generates well-structured review papers in Markdown format, including:

- Title and introduction
- Background and theoretical foundations
- Methodology overview
- Key findings and analysis
- Discussion of implications
- Conclusion and future directions
- Properly formatted references

## 🔧 Customization

You can customize the review paper generation by modifying:
- The agent prompts in `agents/`
- The task definitions in `tasks/`
- The retrieval parameters in `tools/retriever.py`

## 📚 Project Structure

- `elegant_research_assistant.py`: Main Streamlit application
- `review_paper_writing_crew_new/`: CrewAI multi-agent system
  - `main.py`: Entry point for the CrewAI system
  - `agents/`: Agent definitions
  - `tools/`: Custom tools for the agents
  - `tasks/`: Task definitions for the CrewAI workflow
  - `utils/`: Utility functions and helpers
- `research_paper_downloader/`: Paper search and download functionality
- `pdf_processor_pymupdf/`: PDF processing and text extraction

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [CrewAI](https://github.com/joaomdmoura/crewAI) for the multi-agent framework
- [Streamlit](https://streamlit.io/) for the web interface
- [Pinecone](https://www.pinecone.io/) for vector database capabilities
- [OpenAI](https://openai.com/) for language models 