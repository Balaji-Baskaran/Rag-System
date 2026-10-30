import json
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.config import BASE_DIR, UPLOAD_DIR
from backend import rag_service as rag

app = FastAPI(title="StudentRAG Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Follow-up conversation history stored in memory
conversation_history: List[Dict[str, str]] = []

# Static & Frontend serving
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
    session_id: Optional[str] = None  # Kept for backward compatibility

@app.post("/api/upload-and-index", tags=["Upload"])
@app.post("/api/upload", tags=["Upload"])
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files allowed.")
    save_path = UPLOAD_DIR / Path(file.filename).name
    save_path.write_bytes(await file.read())
    count = rag.index_pdf(save_path)
    return {"message": f"'{file.filename}' indexed ({count} chunks)", "filename": file.filename}

@app.post("/api/query/stream", tags=["Chat"])
def query_stream(req: QueryReq):
    docs = rag.vectorstore.similarity_search(req.question, k=4)
    sources = sorted(list({d.metadata.get("source") for d in docs if d.metadata.get("source")}))
    
    # Use client-provided history or server-side memory for follow-up context
    recent_history = req.history if req.history is not None else conversation_history[-6:]
    prompt = rag.build_prompt(req.question, recent_history, docs)

    def event_stream():
        yield f"event: meta\ndata: {json.dumps({'sources': sources})}\n\n"
        full_tokens = []
        for token in rag.stream_llm(prompt):
            full_tokens.append(token)
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        full_answer = "".join(full_tokens)
        
        # Save to history for subsequent follow-up questions
        conversation_history.append({"role": "human", "content": req.question})
        conversation_history.append({"role": "ai", "content": full_answer})
        yield f"event: done\ndata: {json.dumps({'answer_found': bool(full_answer)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/chat", tags=["Chat"])
def chat_sync(req: QueryReq):
    docs = rag.vectorstore.similarity_search(req.question, k=4)
    sources = sorted(list({d.metadata.get("source") for d in docs if d.metadata.get("source")}))
    recent_history = req.history if req.history is not None else conversation_history[-6:]
    prompt = rag.build_prompt(req.question, recent_history, docs)
    answer = rag.call_llm(prompt)
    
    conversation_history.append({"role": "human", "content": req.question})
    conversation_history.append({"role": "ai", "content": answer})
    return {"answer": answer, "sources": sources}

@app.post("/api/chat/clear", tags=["Chat"])
@app.post("/api/session/clear", tags=["Chat"])
def clear_chat(payload: Optional[dict] = None):
    conversation_history.clear()
    return {"message": "Chat history cleared", "cleared": 1}

@app.get("/api/health", tags=["Health"])
def health():
    count = rag.vectorstore._collection.count()
    return {"status": "ok", "collection_status": "ready", "total_chunks": count}

@app.get("/api/stats", tags=["Health"])
def stats():
    meta = rag.vectorstore._collection.get(include=["metadatas"]).get("metadatas") or []
    return {"sources": sorted(list({m["source"] for m in meta if m and "source" in m}))}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=5000, reload=True)