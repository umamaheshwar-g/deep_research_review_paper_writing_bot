# 📚 Research Paper Finder

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.24%2B-red)
![OpenAI](https://img.shields.io/badge/OpenAI-API-orange)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-lightgrey)

A powerful Streamlit-based application for discovering, downloading, and analyzing research papers using advanced semantic search capabilities.

[Features](#features) • [Prerequisites](#prerequisites) • [Installation](#installation) • [Usage](#usage) • [Documentation](#documentation)

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

## 🚀 Prerequisites

- Python 3.7 or higher
- Pinecone API key ([Get here](https://www.pinecone.io/))
- OpenAI API key ([Get here](https://platform.openai.com/))

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
PINECONE_API_KEY=your_pinecone_api_key
OPENAI_API_KEY=your_openai_api_key
```

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

## 📁 Project Structure

```
research-paper-finder/
├── 📜 final_script.py          # Main application script
├── 📂 research_paper_downloader/ # Paper downloading module
├── 📄 pdf_processor_pymupdf.py  # PDF processing module
├── 📋 requirements.txt         # Project dependencies
├── 🔑 .env                    # Environment variables (not in git)
└── 📁 downloads/              # Downloaded papers and processed data
    └── {session-uuid}/
        ├── 📚 papers/         # Downloaded PDF files
        └── 🔍 processed_data/ # Processed paper data
```

## 📚 Documentation

### Workflow Steps

1. **Paper Discovery & Download**
   - Search across academic sources
   - Smart filtering and relevance scoring
   - Concurrent downloads with progress tracking

2. **PDF Processing**
   - Text and metadata extraction
   - Smart content analysis
   - Structured data generation

3. **Vector Indexing**
   - Document chunking
   - Embedding generation
   - Pinecone vector storage

4. **Semantic Search**
   - Query vectorization
   - Similarity matching
   - Relevance-based results

### Command Line Options

#### PDF Processor
```bash
python pdf_processor_pymupdf.py [OPTIONS]
  --folder        PDF files directory
  --output        Output directory
  --uuid          Session UUID
  --processes     Number of processes
  --remove-stopwords  Remove stopwords (default: True)
```

#### Vector Indexing
```bash
python pinecone_indexer.py [OPTIONS]
  --folder        Processed data directory
  --uuid          Index name
  --chunk-size    Chunk size (default: 1000)
  --chunk-overlap Overlap size (default: 200)
```

#### Semantic Search
```bash
python pinecone_query.py [OPTIONS]
  --index         Pinecone index name
  --query         Search query
  --top-k        Number of results (default: 5)
```

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

Made with ❤️ by [Your Name]

</div> 