import logging
from flask import Blueprint, jsonify
from config import MODEL_NAME, API_KEY
from rag_core.state import rag

log = logging.getLogger("studentrag.api.health")
health_bp = Blueprint("health", __name__)

@health_bp.route("/health")
def health():
    chunks, col = 0, "initialising"
    if rag.ready and rag.vectorstore:
        try: chunks = rag.vectorstore._collection.count(); col = "ready"
        except Exception: col = "error"
    elif rag.init_error: col = "error"
    return jsonify(status="ok" if rag.ready else "initialising",
                   llm_configured=bool(API_KEY and API_KEY.startswith("sk-")),
                   collection_status=col, total_chunks=chunks, model=MODEL_NAME)

@health_bp.route("/stats")
def stats():
    sources = []
    if rag.ready and rag.vectorstore:
        try:
            metas = rag.vectorstore._collection.get(include=["metadatas"]).get("metadatas") or []
            sources = sorted({(m or {}).get("source", "") for m in metas} - {""})
        except Exception as e:
            log.warning("stats error: %s", e)
    return jsonify(sources=sources)
