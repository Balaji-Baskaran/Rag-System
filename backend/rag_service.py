import json, requests
from pathlib import Path
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from backend.config import CHROMA_DIR, API_KEY, MODEL_NAME

embeddings  = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings, collection_name="rag_docs")

def index_pdf(file_path: Path) -> int:
    reader = PdfReader(str(file_path))
    docs = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            docs.append(Document(page_content=text, metadata={"source": file_path.name, "page_num": i + 1}))
    if not docs:
        return 0
    splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    vectorstore.add_documents(chunks)
    return len(chunks)

def build_prompt(question: str, history: list, docs: list) -> str:
    history_str = "\n".join([f"{'Student' if m['role']=='human' else 'Assistant'}: {m['content']}" for m in history])
    context_str = "\n\n".join([f"[Source: {d.metadata.get('source')} | Page {d.metadata.get('page_num', 'N/A')}]:\n{d.page_content}" for d in docs])
    return f"""You are an expert study assistant. Using the context and conversation history below, give a thorough answer.
If the student asks a follow-up question, refer to the conversation history for context.

Conversation History:
{history_str}

Context from documents:
{context_str}

Question: {question}
Detailed Answer:"""

def stream_llm(prompt: str):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "stream": True, "max_tokens": 4096}
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, stream=True, timeout=90)
    for line in res.iter_lines(decode_unicode=True):
        if line and line.startswith("data:"):
            body = line[5:].strip()
            if body == "[DONE]":
                break
            try:
                token = json.loads(body)["choices"][0]["delta"].get("content", "")
                if token:
                    yield token
            except Exception:
                continue

def call_llm(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096}
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=90)
    return res.json()["choices"][0]["message"]["content"]

