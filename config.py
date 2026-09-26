import os, logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR        = Path(__file__).parent
CHROMA_DB_PATH  = str(BASE_DIR / "chroma_db" / "rag_docs")
COLLECTION_NAME = "rag_docs"
UPLOAD_DIR      = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Embedding & Chunking
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE      = int(os.environ.get("CHUNK_SIZE", 1024))
CHUNK_OVERLAP   = int(os.environ.get("CHUNK_OVERLAP", 200))
TOP_K           = int(os.environ.get("TOP_K", 10))

# LLM / OpenRouter
API_KEY    = os.environ.get("OPENROUTER_API_KEY", "")
MODEL_NAME = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 4096))

# MySQL (XAMPP)
MYSQL_HOST     = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT     = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER     = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "studentrag")
MEMORY_MAX_MESSAGES = int(os.environ.get("MEMORY_MAX_MESSAGES", 20))

# Upload
ALLOWED_EXT = {".pdf"}

# Prompts
PROMPT_TEMPLATE = """\
You are an expert study assistant. Using ONLY the context provided below,
give a thorough and detailed answer to the question.
- Be comprehensive, detailed, and well-structured.
- Use clear headings, bullet points or numbered lists.
- If the answer is not in the context, say "I don't have enough information in the uploaded documents."
- If the student refers to something from the conversation history, use that context for a coherent follow-up.

{chat_history_block}
Context:
{context}

Question: {question}

Detailed Answer:"""

SUMMARIZE_PROMPT_TEMPLATE = """\
You are an expert academic summariser. Produce a comprehensive, structured summary of ALL the content below.
- Use clear headings and bullet points for key findings.

Context:
{context}

Comprehensive Summary:"""

# Logging
LOG_LEVEL  = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"

def configure_logging():
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format=LOG_FORMAT)
