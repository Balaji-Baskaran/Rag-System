<h1 align="center">RAG SYSTEM</h1>

This is a modular Retrieval-Augmented Generation (RAG) system built with Flask, Langchain, and ChromaDB. It allows users to upload PDF documents, index them, and ask questions based on the content of the documents.
<div align="center">

<img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JavaScript-blue?style=for-the-badge">
<img src="https://img.shields.io/badge/Backend-Python%20(Flask)-green?style=for-the-badge">
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
- **Conversation Memory**: Multi-turn chat memory and session history backed by MySQL (with automatic in-memory fallback).
- **Background Processing**: Handles document indexing asynchronously.
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
                │     Ask Question     │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │  Semantic Search     │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │  Prompt to LLM with  │
                │   Query & Retrieved  │
                │       Context        │
                └─────────┬────────────┘
                          ↓
                ┌──────────────────────┐
                │     LLM Response     │
                └──────────────────────┘

---

## Tech Stack

- HTML,CSS and JS
- Python (Flask)
- langchain
- sentence-tranformer
- chromadb
- pypdf

---

##  Embedded Model 

- The embedding model used is all-MiniLM-L6-v2.
  Why?
  - It allows the system to convert text to vectors and perform semantic search
  - Easy to setup and use
  - Helps for Similiarity search

---

##  Vector Database

- The Vector Database used is Chroma db.
  Why?
  - Native LangChain Support
  - It is extremely fast and lightweight
  - Without need of CPU
    
---

## Application Preview

<img width="1919" height="979" alt="image" src="https://github.com/user-attachments/assets/9a6f0e10-63d3-47bb-8ea6-bed2004a23e9" />

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
   Create a `.env` file in the root directory and add your OpenRouter API key and MySQL settings (optional):
   ```ini
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=openai/gpt-4o-mini
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   CHUNK_SIZE=1024
   CHUNK_OVERLAP=200

   # MySQL settings (optional, defaults to root@localhost:3306)
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_DATABASE=studentrag
   ```

5. **Initialize Database (Optional for MySQL):**
   ```bash
   python setup_db.py
   ```
   *(If MySQL is not running, the application will automatically fall back to in-memory session memory).*

6. **Run the Application:**
   ```bash
   python app.py
   ```
   The application will run on `http://127.0.0.1:5000/`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
