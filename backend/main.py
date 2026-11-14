import json
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.config import BASE_DIR, UPLOAD_DIR
from backend import rag_service as rag
from backend import database as db

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield

app = FastAPI(title="StudentRAG Backend (LlamaIndex + Hybrid Retrieval)", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

static_dir = BASE_DIR / "frontend" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", tags=["Frontend"])
def serve_index():
    index_file = BASE_DIR / "frontend" / "templates" / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "StudentRAG API is running"}

class QueryReq(BaseModel):
    question: str
    history: Optional[List[Dict[str, str]]] = None
    session_id: Optional[str] = None
    mode: Optional[str] = "hybrid"   # 'hybrid', 'dense', or 'sparse'
    top_k: Optional[int] = 4
    alpha: Optional[float] = 0.5    # Dense weight for RRF (0.0 to 1.0)

@app.post("/api/upload-and-index", tags=["Upload"])
@app.post("/api/upload", tags=["Upload"])
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files allowed.")
    save_path = UPLOAD_DIR / Path(file.filename).name
    save_path.write_bytes(await file.read())
    count = rag.index_pdf(save_path)
    if count == 0:
        raise HTTPException(
            status_code=400,
            detail=f"'{file.filename}' contains no readable digital text (0 characters extracted). The PDF is made of scanned images or photos, so 0 chunks were created or loaded into the vector database."
        )
    return {
        "message": f"'{file.filename}' indexed ({count} chunks into Dense & BM25 indexes)",
        "filename": file.filename,
        "chunks": count
    }

@app.post("/api/query/stream", tags=["Chat"])
def query_stream(req: QueryReq):
    session_id = req.session_id or "default"
    mode = req.mode or "hybrid"
    top_k = req.top_k or 4
    alpha = req.alpha if req.alpha is not None else 0.5

    nodes = rag.retrieve_nodes(req.question, top_k=top_k, mode=mode, alpha=alpha)
    sources = sorted(list({n.node.metadata.get("source") for n in nodes if n.node.metadata.get("source")}))
    recent_history = req.history if req.history is not None else db.get_history(session_id, limit=6)
    prompt = rag.build_prompt(req.question, recent_history, nodes)

    def event_stream():
        yield f"event: meta\ndata: {json.dumps({'sources': sources, 'mode': mode})}\n\n"
        full_tokens = []
        try:
            for token in rag.stream_llm(prompt):
                full_tokens.append(token)
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"
            return

        full_answer = "".join(full_tokens)
        if full_answer:
            db.save_message(session_id, "human", req.question)
            db.save_message(session_id, "ai", full_answer)
        yield f"event: done\ndata: {json.dumps({'answer_found': bool(full_answer)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/chat", tags=["Chat"])
def chat_sync(req: QueryReq):
    session_id = req.session_id or "default"
    mode = req.mode or "hybrid"
    top_k = req.top_k or 4
    alpha = req.alpha if req.alpha is not None else 0.5

    nodes = rag.retrieve_nodes(req.question, top_k=top_k, mode=mode, alpha=alpha)
    sources = sorted(list({n.node.metadata.get("source") for n in nodes if n.node.metadata.get("source")}))
    recent_history = req.history if req.history is not None else db.get_history(session_id, limit=6)
    prompt = rag.build_prompt(req.question, recent_history, nodes)
    answer = rag.call_llm(prompt)
    
    db.save_message(session_id, "human", req.question)
    db.save_message(session_id, "ai", answer)
    return {"answer": answer, "sources": sources, "retrieval_mode": mode}

@app.post("/api/retrieve", tags=["Retrieval"])
def retrieve_inspect(req: QueryReq):
    """Inspect retrieved chunks and scores without invoking the LLM."""
    mode = req.mode or "hybrid"
    top_k = req.top_k or 4
    alpha = req.alpha if req.alpha is not None else 0.5
    nodes = rag.retrieve_nodes(req.question, top_k=top_k, mode=mode, alpha=alpha)
    results = [
        {
            "rank": i + 1,
            "id": getattr(n.node, "node_id", None) or getattr(n.node, "id_", None),
            "score": round(float(n.score), 6) if n.score is not None else None,
            "source": n.node.metadata.get("source", "Unknown"),
            "page": n.node.metadata.get("page_num", "N/A"),
            "text": n.node.get_content()
        }
        for i, n in enumerate(nodes)
    ]
    return {
        "question": req.question,
        "mode": mode,
        "alpha": alpha,
        "count": len(results),
        "results": results
    }

@app.get("/api/history/{session_id}", tags=["Chat"])
def get_session_history(session_id: str):
    return {"session_id": session_id, "history": db.get_history(session_id, limit=50)}

@app.get("/api/sessions", tags=["Chat"])
def get_sessions():
    return {"sessions": db.list_sessions(limit=30)}

@app.post("/api/chat/clear", tags=["Chat"])
@app.post("/api/session/clear", tags=["Chat"])
def clear_chat(payload: Optional[dict] = None):
    session_id = (payload or {}).get("session_id", "default")
    db.clear_history(session_id)
    return {"message": f"Chat history for session '{session_id}' cleared", "cleared": 1}

@app.get("/api/health", tags=["Health"])
def health():
    dense_count = rag.chroma_collection.count()
    bm25_count = len(rag.all_nodes)
    return {
        "status": "ok",
        "collection_status": "ready",
        "total_chunks": dense_count,
        "bm25_chunks": bm25_count,
        "retrieval_mode": "hybrid (QueryFusionRetriever + BM25Retriever via RRF)"
    }

@app.get("/api/stats", tags=["Health"])
def stats():
    meta = rag.chroma_collection.get(include=["metadatas"]).get("metadatas") or []
    return {"sources": sorted(list({m["source"] for m in meta if m and "source" in m}))}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=5000, reload=True)
