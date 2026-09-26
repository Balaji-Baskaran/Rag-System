import logging
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config import CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL

log = logging.getLogger("studentrag.vectorstore")

def load_embeddings():
    log.info("Loading embedding model: %s", EMBEDDING_MODEL)
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

def build_vectorstore(embeddings):
    vs = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings,
                collection_name=COLLECTION_NAME)
    count = vs._collection.count()
    log.info("Vectorstore ready (%d chunks)", count)
    return vs
