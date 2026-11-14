<h1 align="center">StudentRAG System</h1>



<div align="center">

<img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JavaScript-blue?style=for-the-badge">
<img src="https://img.shields.io/badge/Backend-Python%20(FastAPI)-green?style=for-the-badge">
<img src="https://img.shields.io/badge/Framework-LlamaIndex-purple?style=for-the-badge">
<img src="https://img.shields.io/badge/VectorDB-ChromaDB-orange?style=for-the-badge">
<img src="https://img.shields.io/badge/Database-MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white">
<img src="https://img.shields.io/badge/LLM-OpenRouter-red?style=for-the-badge">
<img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge">

</div>

<p align="center">
  A high-performance, modular Retrieval-Augmented Generation (RAG) system powered by <strong>FastAPI</strong>, <strong>LlamaIndex</strong>, <strong>ChromaDB</strong>, and <strong>MySQL</strong>. Upload PDF study materials, index them with local dense embeddings, and have interactive multi-turn conversations with source citations and token streaming.
</p>

---

## ✨ Key Features

- **Document Ingestion & Chunking**: Upload PDF documents with automatic page-aware chunking via LlamaIndex `SentenceSplitter`.
- **Hybrid Document Retrieval**: Semantic vector search with ChromaDB and BM25 keyword matching for finding relevant study material.
- **Local Embedding Generation**: Generates dense embeddings locally using `sentence-transformers/all-MiniLM-L6-v2` with zero per-query embedding API costs.
- **Persistent Vector Store**: ChromaDB vector index persists embeddings across server restarts.
- **LLM Streaming (SSE)**: Real-time response generation using Server-Sent Events with OpenRouter API.
- **Conversation History & Session Persistence**: Multi-session chat support with persistent history stored in MySQL database.
- **Precise Citation**: Contextual metadata tracking including document names and page numbers in retrieved citations.
- **Clean Responsive UI**: Modern glassmorphic dark interface with real-time markdown parsing and sidebar session switching.

---

## 🏗️ System Architecture

```text
               ┌───────────────────────────────┐
               │         Upload PDF            │
               └──────────────┬────────────────┘
                              ↓
               ┌───────────────────────────────┐
               │    Text Extraction (pypdf)    │
               │   & Chunking (LlamaIndex)     │
               └──────────────┬────────────────┘
                              ↓
               ┌───────────────────────────────┐
               │  Embeddings (HuggingFace)     │
               │   all-MiniLM-L6-v2            │
               └──────────────┬────────────────┘
                              ↓
               ┌───────────────────────────────┐
               │      ChromaDB Vector Store    │
               └──────────────┬────────────────┘
                              ↓
   ┌────────────────────────────────────────────────────────┐
   │                  User Chat Query                       │
   └──────────────────────────┬─────────────────────────────┘
                              ↓
   ┌────────────────────────────────────────────────────────┐
   │ 1. Retrieve relevant chunks (ChromaDB & BM25)          │
   │ 2. Fetch conversation history for session (MySQL)      │    
   └──────────────────────────┬─────────────────────────────┘
                              ↓
   ┌────────────────────────────────────────────────────────┐
   │                     Frontend                           │
   └────────────────────────────────────────────────────────┘
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.9+
- MySQL Server (optional but recommended for persistent chat history)
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))

### 2. Clone the Repository
```bash
git clone https://github.com/Balaji-Baskaran/Rag-System.git
cd Rag-System
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Edit `.env`:
```ini
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=rag_db
```

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 📸 Application Preview

<p align="center">
  <img width="1915" height="970" alt="StudentRAG Preview" src="https://github.com/user-attachments/assets/ffc67888-cf94-497d-bb64-96a35c55e2c1" />
</p>

---
