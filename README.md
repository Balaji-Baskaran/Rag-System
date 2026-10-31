<h1 align="center">StudentRAG System</h1>

<p align="center">
  A high-performance, modular Retrieval-Augmented Generation (RAG) system powered by <strong>FastAPI</strong>, <strong>LlamaIndex</strong>, <strong>ChromaDB</strong>, and <strong>MySQL</strong>. Upload PDF study materials, index them with local dense embeddings, and have interactive multi-turn conversations with source citations and token streaming.
</p>

<div align="center">

<img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JavaScript-blue?style=for-the-badge">
<img src="https://img.shields.io/badge/Backend-Python%20(FastAPI)-green?style=for-the-badge">
<img src="https://img.shields.io/badge/Framework-LlamaIndex-purple?style=for-the-badge">
<img src="https://img.shields.io/badge/VectorDB-ChromaDB-orange?style=for-the-badge">
<img src="https://img.shields.io/badge/Database-MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white">
<img src="https://img.shields.io/badge/LLM-OpenRouter-red?style=for-the-badge">
<img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge">
</div>

--- 

## System Architecture

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
   │ 1. Retrieve top-k semantic chunks (ChromaDB)           │
   │ 2. Fetch conversation history for session (MySQL)       │
   │ 3. Build enriched context prompt                       │
   └──────────────────────────┬─────────────────────────────┘
                              ↓
   ┌────────────────────────────────────────────────────────┐
   │     OpenRouter API Stream (SSE) -> Frontend UI         │
   └────────────────────────────────────────────────────────┘
```

---


## Setup & Installation

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
cp .env.example .env
```

Edit `.env`:
```ini
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=port_number
MYSQL_USER=your_user_name
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=rag_db
```

*(Note: If MySQL is not running or credentials are empty, the backend logs a warning and session memory falls back gracefully.)*

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## Application Preview

<img width="1915" height="970" alt="image" src="https://github.com/user-attachments/assets/ffc67888-cf94-497d-bb64-96a35c55e2c1" />

---
