import logging, threading
from config import API_KEY, MODEL_NAME, MAX_TOKENS

log = logging.getLogger("studentrag.state")

class RAGState:
    def __init__(self):
        self.embeddings = self.vectorstore = self.llm = self.qa_chain = None
        self.ready = False
        self.init_error = None
        self.lock = threading.Lock()

rag = RAGState()

def _initialise_rag():
    from rag_core.llm import OpenRouterLLM
    from rag_core.vectorstore import load_embeddings, build_vectorstore
    from rag_core.chain import build_qa_chain
    try:
        rag.embeddings  = load_embeddings()
        rag.vectorstore = build_vectorstore(rag.embeddings)
        rag.llm         = OpenRouterLLM(api_key=API_KEY, model=MODEL_NAME, max_tokens=MAX_TOKENS)
        rag.qa_chain, _ = build_qa_chain(rag.vectorstore, rag.llm)
        rag.ready = True
        log.info("RAG system initialised ✓")
    except Exception as exc:
        rag.init_error = str(exc)
        log.error("RAG init failed: %s", exc, exc_info=True)

def start_rag_init():
    threading.Thread(target=_initialise_rag, name="rag-init", daemon=True).start()
    log.info("RAG init thread started")
