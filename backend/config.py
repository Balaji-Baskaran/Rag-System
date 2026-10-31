import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

CHROMA_DIR = str(BASE_DIR / "chroma_db" / "rag_docs")
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

API_KEY    = os.getenv("OPENROUTER_API_KEY", "").strip().strip('"').strip("'")
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip().strip('"').strip("'")

# MySQL Configuration
MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost").strip().strip('"').strip("'")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306").strip().strip('"').strip("'") or 3306)
MYSQL_USER     = os.getenv("MYSQL_USER", "root").strip().strip('"').strip("'")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "").strip().strip('"').strip("'")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "rag_db").strip().strip('"').strip("'")
