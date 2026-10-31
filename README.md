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

## ✨ Key Features

- **Document Ingestion & Chunking**: Upload PDF documents with automatic page-aware chunking via LlamaIndex `SentenceSplitter`.
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

## 🛠️ Tech Stack

- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3, Marked.js (Markdown renderer)
- **Backend**: FastAPI, Uvicorn, Python-Multipart
- **RAG & Search**: LlamaIndex, Sentence-Transformers, ChromaDB, PyPDF
- **Database**: MySQL (PyMySQL) for conversation session persistence
- **LLM Provider**: OpenRouter (`openai/gpt-4o-mini` or any compatible model)

---

## 📁 Project Structure

```text
rag-system/
├── backend/
│   ├── __init__.py
│   ├── config.py         # Environment configuration and directory paths
│   ├── database.py       # MySQL connection pool and session memory
│   ├── main.py           # FastAPI server and streaming endpoints
│   └── rag_service.py    # LlamaIndex vector store, indexing, and LLM calls
├── frontend/
│   ├── static/
│   │   ├── css/style.css # UI styles
│   │   └── js/app.js     # Chat state, SSE stream handler, and UI actions
│   └── templates/
│       └── index.html    # Single-page interface
├── notebook/
│   └── rag_system.ipynb  # Interactive RAG experimentation notebook
├── uploads/              # Uploaded PDF files (git-ignored)
├── .env.example          # Environment variables template
├── .gitignore            # Git exclusion rules
├── app.py                # Application entrypoint
├── requirements.txt      # Python dependencies
└── README.md
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

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web interface |
| `POST` | `/api/upload` | Uploads and indexes a PDF document |
| `POST` | `/api/query/stream` | Stream chat completions with citations via SSE |
| `POST` | `/api/chat` | Synchronous chat query endpoint |
| `GET` | `/api/history/{session_id}` | Fetch conversation history for a given session |
| `GET` | `/api/sessions` | List recent conversation sessions |
| `POST` | `/api/chat/clear` | Clear chat history for a session |
| `GET` | `/api/health` | Returns health status and indexed chunks count |
| `GET` | `/api/stats` | Returns indexed source documents |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
