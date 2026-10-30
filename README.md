<h1 align="center">RAG SYSTEM</h1>

This is a modular Retrieval-Augmented Generation (RAG) system built with FastAPI, Langchain, and ChromaDB. It allows users to upload PDF documents, index them, and ask questions and follow-ups based on the content of the documents.
<div align="center">

<img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JavaScript-blue?style=for-the-badge">
<img src="https://img.shields.io/badge/Backend-Python%20(FastAPI)-green?style=for-the-badge">
<img src="https://img.shields.io/badge/Framework-LangChain-purple?style=for-the-badge">
<img src="https://img.shields.io/badge/VectorDB-ChromaDB-orange?style=for-the-badge">
<img src="https://img.shields.io/badge/LLM-OpenRouter-red?style=for-the-badge">
<img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge">
</div>

--- 

## Features

- **Upload PDFs**: Simple endpoint to upload PDF documents.
- **RAG Engine**: Uses Langchain to chunk and embed documents using `sentence-transformers`.
- **Vector Database**: Uses ChromaDB to store document embeddings for fast retrieval.
- **LLM Integration**: Uses OpenRouter to generate answers based on the retrieved context from your documents.
- **Follow-up Conversation Memory**: Maintains recent conversation turns in memory so you can ask coherent follow-up questions without needing an external database.
- **Streaming Responses**: Real-time token streaming using Server-Sent Events (SSE).
- **RESTful API**: Structured and modularized API routes.

---

## System Architecture

                ┌──────────────────────┐
                │   Upload PDF         │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │  PDF Cleaning &      │
                │          Indexing    │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │    Text Chunking     │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │   Embedding Model    │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │     Vector DB        │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │ Ask Question / Follow-up │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │  Semantic Search     │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │  Prompt to LLM with  │
                │   Query, History, &  │
                │   Retrieved Context  │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │     LLM Response     │
                └──────────────────────┘

---

## Tech Stack

- HTML, CSS and JS
- Python (FastAPI)
- langchain
- sentence-transformers
- chromadb
- pypdf

---

## Embedded Model 

- The embedding model used is `all-MiniLM-L6-v2`.
  Why?
  - It allows the system to convert text to vectors and perform semantic search
  - Easy to setup and use
  - Fast similarity search

---

## Vector Database

- The Vector Database used is ChromaDB.
  Why?
  - Native LangChain Support
  - Extremely fast and lightweight
  - Runs locally without CPU overhead
    
---

## Application Preview

<img width="1913" height="960" alt="image" src="https://github.com/user-attachments/assets/88a2fa8f-1a87-47bd-bc16-4ace4d7e6b26" />

---

## Prerequisites

- Python 3.9+
- [OpenRouter](https://openrouter.ai/) API Key

---

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Balaji-Baskaran/Rag-System.git
   cd Rag-System
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add your OpenRouter API key:
   ```ini
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=openai/gpt-4o-mini
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   CHUNK_SIZE=1024
   CHUNK_OVERLAP=200
   ```

5. **Run the Application:**
   ```bash
   python app.py
   # or
   python -m backend.main
   ```
   The application will run on `http://127.0.0.1:5000/`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
