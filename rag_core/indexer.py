import logging
from pathlib import Path
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP

log = logging.getLogger("studentrag.indexer")

def load_pdf(pdf_path):
    reader = PdfReader(str(pdf_path))
    docs = [Document(page_content=text, metadata={"source": pdf_path.name, "page_num": i+1, "total_pages": len(reader.pages)})
            for i, page in enumerate(reader.pages) if (text := (page.extract_text() or "").strip())]
    log.info("Loaded %d pages from '%s'", len(docs), pdf_path.name)
    return docs

def chunk_documents(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = [doc for doc in splitter.split_documents(docs)
              if (doc.page_content or "").strip()]
    for c in chunks:
        c.page_content = c.page_content.encode("utf-8", errors="ignore").decode("utf-8")
    log.info("Produced %d chunks", len(chunks))
    return chunks

def index_pdf(pdf_path, rag_state):
    from rag_core.chain import build_qa_chain
    if not rag_state.ready:
        raise RuntimeError("RAG system not ready yet.")
    raw_docs = load_pdf(pdf_path)
    if not raw_docs:
        raise ValueError(f"No extractable text in '{pdf_path.name}'.")
    chunks = chunk_documents(raw_docs)
    with rag_state.lock:
        rag_state.vectorstore.add_documents(chunks)
        rag_state.qa_chain, _ = build_qa_chain(rag_state.vectorstore, rag_state.llm)
    log.info("Indexed %d chunks from '%s'", len(chunks), pdf_path.name)
    return len(chunks)
