# 📚 Research Paper Finder

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.24%2B-red)
![OpenAI](https://img.shields.io/badge/OpenAI-API-orange)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-lightgrey)

A powerful Streamlit-based application for discovering, downloading, and analyzing research papers using advanced semantic search capabilities.

[Features](#features) • [Prerequisites](#prerequisites) • [Usage](#usage) • [Documentation](#documentation) • [Installation](#installation) • [Contributing](#contributing)

</div>

---

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

## 🚀 Prerequisites

- Python 3.7 or higher
- Pinecone API key ([Get here](https://www.pinecone.io/))
- OpenAI API key ([Get here](https://platform.openai.com/))

## 📖 Usage

### Web Interface

1. **Start the application**
```bash
streamlit run final_script.py
```

2. **Use the interface**
- Enter your research query
- Adjust search parameters in the sidebar
- Click "Search and Download"
- Save the generated UUID for future reference

### Command Line Interface

Process papers from existing sessions:
```bash
python final_script.py --uuid YOUR_SESSION_UUID --process
```

### Review Paper Generation

Generate comprehensive research review papers:
```bash
# Activate the virtual environment
# Windows
.\venv\Scripts\Activate.ps1

# Generate a review paper on a specific topic
python review_paper_writing_crew_new/main.py --topic "Your Research Topic" --output review_paper.md

# Use an existing Pinecone namespace
python review_paper_writing_crew_new/main.py --topic "Your Research Topic" --namespace YOUR_NAMESPACE --output review_paper.md
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
   - Try printing the environment variables to debug:
     ```python
     import os
     from dotenv import load_dotenv
     load_dotenv()
     print(f"OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")
     print(f"PINECONE_API_KEY set: {bool(os.getenv('PINECONE_API_KEY'))}")
     ```

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
   - Ensure you're using the correct API key format for each service

## 📁 Project Structure

```
research-paper-finder/
├── 📜 final_script.py          # Main application script
├── 📂 research_paper_downloader/ # Paper downloading module
├── 📄 pdf_processor_pymupdf.py  # PDF processing module
├── 📋 requirements.txt         # Project dependencies
├── 🔑 .env                    # Environment variables (not in git)
├── 🔑 .env.toml               # Alternative TOML-format environment config (optional)
├── 📂 review_paper_writing_crew_new/ # AI-powered research paper writing module
│   ├── 📜 main.py             # Main entry point for the review paper generation
│   ├── 🔑 .env                # Module-specific environment variables (optional)
│   ├── 🔑 .env.example        # Example environment file for the module
│   ├── 📂 agents/             # CrewAI agent definitions
│   │   ├── 📄 manager_agent.py # Oversees the entire paper generation process
│   │   ├── 📄 researcher_agent.py # Retrieves and analyzes research papers
│   │   ├── 📄 writer_agent.py  # Drafts sections of the review paper
│   │   └── 📄 editor_agent.py  # Refines and polishes the final paper
│   ├── 📂 tasks/              # Task definitions for each agent
│   │   ├── 📄 research_tasks.py # Tasks for literature search and analysis
│   │   ├── 📄 writing_tasks.py # Tasks for drafting paper sections
│   │   └── 📄 editing_tasks.py # Tasks for editing and refinement
│   ├── 📂 tools/              # Custom tools for agents
│   │   ├── 📄 retriever.py    # Pinecone vector search tool
│   │   └── 📄 citation_manager.py # Manages paper citations
│   └── 📂 utils/              # Utility functions
│       └── 📄 helpers.py      # Helper functions for the module
└── 📁 downloads/              # Downloaded papers and processed data
    └── {session-uuid}/
        ├── 📚 papers/         # Downloaded PDF files
        └── 🔍 processed_data/ # Processed paper data
```

### 🔑 Environment File Management

The project uses environment variables for configuration and API keys. There are several environment files:

1. **Root `.env`**: Main configuration file in the project root
   - Contains all API keys and configuration settings
   - Used by all components unless overridden

2. **Module-specific `.env` files**:
   - `research_paper_downloader/.env`: Settings for the paper downloader
   - `review_paper_writing_crew_new/.env`: Settings for the review paper generator

3. **Alternative formats**:
   - `.env.toml`: TOML-format configuration (more structured)
   - `.env.example`: Example configuration templates

For most users, creating a single `.env` file in the project root with all required variables is sufficient.

## 📚 Documentation

### 🔄 Workflow Steps

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

#### 📥 1. Paper Discovery & Download

<table>
<tr>
<td width="80"><h1 align="center">🔍</h1></td>
<td>

- **Multi-Source Search**: Queries academic databases and repositories to find relevant papers
- **Smart Filtering**: Uses AI-powered relevance scoring to prioritize the most important papers
- **Concurrent Downloads**: Implements asynchronous downloading with progress tracking
- **Metadata Extraction**: Automatically extracts titles, authors, publication dates, and abstracts
- **Format Handling**: Supports PDF documents with automatic format validation

</td>
</tr>
</table>

#### 📊 2. PDF Processing

<table>
<tr>
<td width="80"><h1 align="center">📄</h1></td>
<td>

- **Text Extraction**: Uses PyMuPDF to extract full text content with layout preservation
- **Structure Recognition**: Identifies sections, headings, figures, and tables
- **Metadata Enhancement**: Enriches document metadata with extracted information
- **Content Analysis**: Performs initial content analysis for quality assessment
- **Multi-Processing**: Utilizes parallel processing for handling multiple documents efficiently

</td>
</tr>
</table>

#### 🧩 3. Vector Indexing

<table>
<tr>
<td width="80"><h1 align="center">🔢</h1></td>
<td>

- **Smart Chunking**: Splits documents into semantic chunks using RecursiveCharacterTextSplitter
- **Embedding Generation**: Creates vector embeddings using OpenAI's text-embedding-3-large model
- **Metadata Preservation**: Maintains document metadata linked to each chunk
- **Batch Processing**: Processes embeddings in optimized batches for efficiency
- **Pinecone Integration**: Stores vectors in Pinecone with namespace-based organization

</td>
</tr>
</table>

#### 🔎 4. Semantic Search

<table>
<tr>
<td width="80"><h1 align="center">🧠</h1></td>
<td>

- **Query Vectorization**: Converts natural language queries into vector representations
- **Similarity Matching**: Performs cosine similarity search across the vector database
- **Context-Aware Results**: Returns results with surrounding context for better understanding
- **Relevance Scoring**: Ranks results based on semantic similarity scores
- **Filtering Capabilities**: Supports filtering by document, section, or custom metadata

</td>
</tr>
</table>

#### 📝 5. AI-Powered Review Paper Generation

<table>
<tr>
<td width="80"><h1 align="center">🤖</h1></td>
<td>

- **Multi-Agent Collaboration**: Orchestrates specialized agents using CrewAI framework
- **Research Workflow**: Implements a structured research process with defined tasks
- **Content Synthesis**: Combines information from multiple sources into coherent sections
- **Citation Management**: Automatically tracks and formats academic citations
- **Quality Control**: Includes editing and refinement phases for academic standards

</td>
</tr>
</table>

### Review Paper Writing Crew Architecture

The `review_paper_writing_crew_new` module is an AI-powered system for automatically generating comprehensive research review papers on any topic. It leverages CrewAI to orchestrate multiple specialized agents working together.

#### Key Components:

1. **Agent System**
   - **Manager Agent**: Oversees the entire paper generation process and coordinates between agents
   - **Researcher Agent**: Conducts literature searches and analyzes research papers using semantic search
   - **Writer Agent**: Drafts sections of the review paper based on research findings
   - **Editor Agent**: Refines and polishes the final paper for clarity and academic standards

2. **Task Workflow**
   - **Research Tasks**: Initial literature search, background development, theme identification, methodology analysis, findings synthesis
   - **Writing Tasks**: Section drafting, introduction creation, methodology description, results presentation, discussion development, conclusion formulation
   - **Editing Tasks**: Content review, citation verification, structural improvement, language refinement

3. **Tools Integration**
   - **PineconeRetriever**: Semantic search tool that connects to Pinecone vector database
   - **Citation Manager**: Handles proper academic citation formatting and tracking

4. **Execution Process**
   - Sequential task execution with memory retention between tasks
   - Namespace-based session management for result persistence
   - Structured output in markdown format with proper academic citations

### ⌨️ Command Line Options

<details>
<summary><b>Review Paper Generator</b></summary>

```bash
python review_paper_writing_crew_new/main.py [OPTIONS]
  --topic         Research topic to review (default: "Diffusion Large Language Models")
  --output        Output filename (default: review_paper.md)
  --namespace     Pinecone namespace (UUID generated if not provided)
  --index-name    Pinecone index name (default: deepresearchreviewbot)
  --debug         Enable debug logging for the retriever
```
</details>

<details>
<summary><b>PDF Processor</b></summary>

```bash
python pdf_processor_pymupdf.py [OPTIONS]
  --folder        PDF files directory
  --output        Output directory
  --uuid          Session UUID
  --processes     Number of processes
  --remove-stopwords  Remove stopwords (default: True)
```
</details>

<details>
<summary><b>Vector Indexing</b></summary>

```bash
python pinecone_indexer.py [OPTIONS]
  --folder        Processed data directory
  --uuid          Index name
  --chunk-size    Chunk size (default: 1000)
  --chunk-overlap Overlap size (default: 200)
```
</details>

<details>
<summary><b>Semantic Search</b></summary>

```bash
python pinecone_query.py [OPTIONS]
  --index         Pinecone index name
  --query         Search query
  --top-k        Number of results (default: 5)
```
</details>

### 📊 Data Flow

The system processes information through a series of transformations:

<table>
<tr>
<th>Stage</th>
<th>Input</th>
<th>Process</th>
<th>Output</th>
</tr>
<tr>
<td><b>Query Processing</b></td>
<td>User research query</td>
<td>Query expansion and optimization</td>
<td>Structured search parameters</td>
</tr>
<tr>
<td><b>Paper Discovery</b></td>
<td>Search parameters</td>
<td>Multi-source academic search</td>
<td>PDF documents + metadata</td>
</tr>
<tr>
<td><b>PDF Processing</b></td>
<td>PDF documents</td>
<td>Text extraction and structure analysis</td>
<td>Structured text content</td>
</tr>
<tr>
<td><b>Chunking</b></td>
<td>Structured text</td>
<td>Semantic chunking with metadata</td>
<td>Text chunks with context</td>
</tr>
<tr>
<td><b>Embedding</b></td>
<td>Text chunks</td>
<td>Vector embedding generation</td>
<td>Vector representations</td>
</tr>
<tr>
<td><b>Indexing</b></td>
<td>Vectors + metadata</td>
<td>Pinecone vector storage</td>
<td>Searchable vector database</td>
</tr>
<tr>
<td><b>Semantic Search</b></td>
<td>Query vectors</td>
<td>Similarity matching</td>
<td>Relevant text chunks</td>
</tr>
<tr>
<td><b>Review Generation</b></td>
<td>Relevant chunks</td>
<td>Multi-agent collaboration</td>
<td>Structured review paper</td>
</tr>
</table>

## 💻 Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/research-paper-finder.git
cd research-paper-finder
```

2. **Set up virtual environment**
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

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

# Pinecone Configuration
PINECONE_INDEX_NAME=your_pinecone_index_name  # Default: deepresearchreviewbot

# Academic API Configuration (for paper discovery)
CROSSREF_EMAIL=your_email@example.com
PUBMED_EMAIL=your_email@example.com
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key
SERPER_API_KEY=your_serper_api_key

# Optional API Keys (for enhanced functionality)
GROQ_API_KEY=your_groq_api_key  # Alternative LLM provider
GEMINI_API_KEY=your_gemini_api_key  # Alternative LLM provider
HF_TOKEN=your_huggingface_token  # For HuggingFace models

# Vector Database Options (Pinecone is required, others optional)
WEAVIATE_URL=your_weaviate_url  # Optional alternative vector DB
WEAVIATE_API_KEY=your_weaviate_api_key
QDRANT_API_KEY=your_qdrant_api_key  # Optional alternative vector DB

# Application Settings
DEBUG=True  # Set to False in production
SAVE_RAW_RESPONSES=True  # Set to False to save storage
```

> **Note**: The project uses multiple `.env` files in different directories. For simplicity, you can create a single `.env` file in the root directory, and it will be used by all components. If you need to customize settings for specific modules, you can create separate `.env` files in the respective directories.

> **Important**: At minimum, you must provide `OPENAI_API_KEY` and `PINECONE_API_KEY` for the application to function properly.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Commit your changes
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. Push to the branch
```bash
   git push origin feature/amazing-feature
   ```
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by Uma Maheshwar Gupta Gunda

</div> 