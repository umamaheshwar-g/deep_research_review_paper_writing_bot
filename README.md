# Research Paper Finder

A Streamlit-based application for searching, downloading, and analyzing research papers using semantic search capabilities.

## Features

- Search and download research papers based on queries
- Process PDF papers and extract content
- Semantic search using Pinecone vector database
- Session management with UUID-based retrieval
- Concurrent downloads with progress tracking
- PDF processing with metadata extraction
- Interactive UI with Streamlit

## Prerequisites

- Python 3.7+
- Pinecone API key
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd research-paper-finder
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your API keys:
```
PINECONE_API_KEY=your_pinecone_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run final_script.py
```

2. Enter your research query in the search box
3. Adjust search parameters in the sidebar
4. Click "Search and Download" to begin
5. Use the generated UUID to retrieve your session later

### Command Line Usage

You can also process papers from the command line:
```bash
python final_script.py --uuid YOUR_SESSION_UUID --process
```

## Project Structure

```
research-paper-finder/
├── final_script.py          # Main application script
├── research_paper_downloader/ # Paper downloading module
├── pdf_processor_pymupdf.py  # PDF processing module
├── requirements.txt         # Project dependencies
├── .env                    # Environment variables (not in git)
└── downloads/              # Downloaded papers and processed data
    └── {session-uuid}/
        ├── papers/         # Downloaded PDF files
        └── processed_data/ # Processed paper data
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Research Paper Processing and Indexing

This repository contains tools for downloading, processing, and indexing research papers for semantic search and retrieval.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following environment variables:

```
GEMINI_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment  # defaults to "gcp-starter"
```

## Workflow

The complete workflow consists of four main steps:

1. **Download research papers** using the `fetch_and_download_flow.py` script
2. **Process the PDFs** using the `pdf_processor_pymupdf.py` script
3. **Index the processed data** in Pinecone using the `pinecone_indexer.py` script
4. **Query the index** using the `pinecone_query.py` script

### 1. Download Research Papers

```bash
python -m research_paper_downloader.fetch_and_download_flow
```

This will:
- Search for papers based on your query
- Evaluate the papers using Gemini
- Download the most relevant papers
- Create a folder structure with a unique chat UUID

### 2. Process PDFs

```bash
python pdf_processor_pymupdf.py --uuid CHAT_UUID
```

Replace `CHAT_UUID` with the UUID generated in step 1.

This will:
- Load the downloaded PDFs
- Extract text and metadata
- Use the smart search results for enhanced metadata
- Save the processed data to JSON files

### 3. Index in Pinecone

```bash
python pinecone_indexer.py --folder PATH_TO_PROCESSED_DATA
```

Replace `PATH_TO_PROCESSED_DATA` with the path to the processed data folder (usually `downloads/CHAT_UUID/processed_data`).

This will:
- Load the processed data
- Chunk the documents
- Generate embeddings
- Create a Pinecone index using the chat UUID
- Upload the vectors to Pinecone

### 4. Query the Index

```bash
python pinecone_query.py --index INDEX_NAME --query "your search query"
```

Replace `INDEX_NAME` with the name of the Pinecone index (usually the chat UUID).

This will:
- Convert your query to an embedding
- Search the Pinecone index for similar vectors
- Return the most relevant chunks with metadata
- Display formatted results with citations and relevance scores

## Command Line Arguments

### PDF Processor

```bash
python pdf_processor_pymupdf.py --help
```

Options:
- `--folder`: Folder containing PDF files
- `--output`: Output folder for processed data
- `--uuid`: UUID of the search to process
- `--processes`: Number of processes to use
- `--remove-stopwords`: Remove stopwords from paper metadata (default: True)
- `--keep-original`: Keep original metadata without removing stopwords

### Pinecone Indexer

```bash
python pinecone_indexer.py --help
```

Options:
- `--folder`: Folder containing processed PDF data (required)
- `--uuid`: UUID to use as the index name (defaults to folder name or generates new)
- `--api-key`: Pinecone API key (defaults to PINECONE_API_KEY env var)
- `--environment`: Pinecone environment (defaults to PINECONE_ENVIRONMENT env var)
- `--chunk-size`: Size of each chunk (default: 1000)
- `--chunk-overlap`: Overlap between chunks (default: 200)

### Pinecone Query

```bash
python pinecone_query.py --help
```

Options:
- `--index`: Name of the Pinecone index to query (required)
- `--query`: Query string (required)
- `--top-k`: Number of results to return (default: 5)
- `--api-key`: Pinecone API key (defaults to PINECONE_API_KEY env var)
- `--environment`: Pinecone environment (defaults to PINECONE_ENVIRONMENT env var)

## Example Usage

Complete workflow example:

```bash
# 1. Download papers
python -m research_paper_downloader.fetch_and_download_flow

# This will output a chat UUID, e.g., chat_abc123_20230615_123456

# 2. Process the PDFs
python pdf_processor_pymupdf.py --uuid chat_abc123_20230615_123456

# 3. Index in Pinecone
python pinecone_indexer.py --folder downloads/chat_abc123_20230615_123456/processed_data

# 4. Query the index
python pinecone_query.py --index chat_abc123_20230615_123456 --query "What are the latest advances in transformer models?"
```

## Notes

- The Pinecone indexer will automatically use the chat UUID as the index name
- If you don't specify a UUID for the Pinecone index, it will try to extract it from the folder path
- The processed data includes evaluation data from the smart search results
- The metadata is preserved in the Pinecone index for better retrieval
- Query results include citations and relevance scores from the original paper evaluation 