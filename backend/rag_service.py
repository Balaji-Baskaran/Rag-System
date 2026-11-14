import json, requests
from pathlib import Path
from pypdf import PdfReader
import chromadb
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.schema import TextNode
from llama_index.core.llms.mock import MockLLM
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from backend.config import CHROMA_DIR, API_KEY, MODEL_NAME

# 1. Initialize HuggingFace Dense Embeddings and ChromaDB Vector Store
hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
embed_kwargs = {"cache_folder": str(hf_cache), "local_files_only": True} if hf_cache.exists() else {}
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2", **embed_kwargs)

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
chroma_collection = chroma_client.get_or_create_collection("rag_docs")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

# 2. Warm In-Memory Nodes for BM25Retriever (ChromaDB stores vectors, not docstore)
def load_all_nodes():
    data = chroma_collection.get(include=["documents", "metadatas"])
    return [
        TextNode(id_=i, text=t, metadata=m or {})
        for i, t, m in zip(data.get("ids", []), data.get("documents", []), data.get("metadatas", []))
        if t
    ]

all_nodes = load_all_nodes()
bm25_retriever = BM25Retriever.from_defaults(nodes=all_nodes, similarity_top_k=4) if all_nodes else None

def index_pdf(file_path: Path) -> int:
    global bm25_retriever, all_nodes
    reader = PdfReader(str(file_path))
    docs = [
        Document(text=text, metadata={"source": file_path.name, "page_num": i + 1})
        for i, page in enumerate(reader.pages)
        if (text := (page.extract_text() or "").strip())
    ]
    if not docs:
        return 0
    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
    nodes = splitter.get_nodes_from_documents(docs)
    
    index.insert_nodes(nodes)
    all_nodes.extend(nodes)
    bm25_retriever = BM25Retriever.from_defaults(nodes=all_nodes, similarity_top_k=4)
    return len(nodes)

def retrieve_nodes(question: str, top_k: int = 4, mode: str = "hybrid", alpha: float = 0.5):
    dense_retriever = index.as_retriever(similarity_top_k=top_k)
    if mode == "dense" or not bm25_retriever:
        return dense_retriever.retrieve(question)

    bm25_retriever.similarity_top_k = top_k
    if mode == "sparse":
        return bm25_retriever.retrieve(question)

    hybrid_retriever = QueryFusionRetriever(
        retrievers=[dense_retriever, bm25_retriever],
        similarity_top_k=top_k,
        num_queries=1,
        mode="reciprocal_rerank",
        use_async=False,
        llm=MockLLM()
    )
    return hybrid_retriever.retrieve(question)

def build_prompt(question: str, history: list, nodes: list) -> str:
    history_str = "\n".join([f"{'Student' if m['role']=='human' else 'Assistant'}: {m['content']}" for m in history])
    context_str = "\n\n".join([
        f"[Source: {n.node.metadata.get('source', 'Unknown')} | Page {n.node.metadata.get('page_num', 'N/A')}]:\n{n.node.get_content()}"
        for n in nodes
    ])
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
    if res.status_code != 200:
        try:
            err = res.json().get("error", {}).get("message", res.text)
        except Exception:
            err = res.text
        raise RuntimeError(f"OpenRouter Error ({res.status_code}): {err}")

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
    if res.status_code != 200:
        try:
            err = res.json().get("error", {}).get("message", res.text)
        except Exception:
            err = res.text
        raise RuntimeError(f"OpenRouter Error ({res.status_code}): {err}")
    return res.json()["choices"][0]["message"]["content"]
