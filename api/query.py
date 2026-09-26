import json, logging, time, uuid
from flask import Blueprint, Response, jsonify, request, stream_with_context
from config import MODEL_NAME, PROMPT_TEMPLATE, SUMMARIZE_PROMPT_TEMPLATE
from rag_core.state import rag
from rag_core.memory import add_message, get_history, clear_session, format_history_for_prompt, list_sessions

log = logging.getLogger("studentrag.api.query")
query_bp = Blueprint("query", __name__)

def _sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

def _retrieve(question, top_k=5, min_score=0.1):
    results = rag.vectorstore.similarity_search_with_relevance_scores(question, k=top_k)
    filtered = [(d, s) for d, s in results if s >= min_score] or results[:top_k]
    return filtered, [d for d, _ in filtered]

def _build_context(docs):
    return "\n\n".join(f"[Source: {d.metadata.get('source','unknown')} | Page {d.metadata.get('page_num','N/A')}]\n{d.page_content}" for d in docs)

def _build_prompt(context, question, session_id=None):
    block = ""
    if session_id:
        h = format_history_for_prompt(get_history(session_id))
        if h: block = f"Conversation History:\n{h}\n\n"
    return PROMPT_TEMPLATE.format(chat_history_block=block, context=context, question=question)

def _chunks_info(filtered):
    return [{"source": d.metadata.get("source","unknown"), "page": d.metadata.get("page_num","N/A"),
             "score": round(float(s),4), "text": d.page_content[:300],
             "chunk_id": f"{d.metadata.get('source','?')}-p{d.metadata.get('page_num','?')}"}
            for d, s in filtered]

def _sources(docs):
    return sorted({d.metadata.get("source","") for d in docs} - {""})

# /api/query (non-streaming)
@query_bp.route("/query", methods=["POST"])
def query():
    if not rag.ready: return jsonify(detail="RAG system is still initialising."), 503
    body = request.get_json(force=True) or {}
    q = (body.get("question") or "").strip()
    if not q: return jsonify(detail="Question cannot be empty."), 400
    sid, t0 = body.get("session_id"), time.time()
    try: filtered, docs = _retrieve(q, int(body.get("top_k",5)), float(body.get("min_score",0.1)))
    except Exception as e: return jsonify(detail=f"Retrieval error: {e}"), 500
    try: answer = rag.llm._call(_build_prompt(_build_context(docs), q, sid))
    except Exception as e: return jsonify(detail=str(e)), 502
    if sid: add_message(sid, "human", q); add_message(sid, "ai", answer)
    return jsonify(answer=answer, answer_found="I don't have enough information" not in answer,
                   sources=_sources(docs), chunks=_chunks_info(filtered),
                   retrieved_count=len(filtered), query_time_ms=round((time.time()-t0)*1000),
                   model_used=MODEL_NAME, session_id=sid)

# /api/query/stream (SSE)
@query_bp.route("/query/stream", methods=["POST"])
def query_stream():
    if not rag.ready: return jsonify(detail="RAG system is still initialising."), 503
    body = request.get_json(force=True) or {}
    q = (body.get("question") or "").strip()
    if not q: return jsonify(detail="Question cannot be empty."), 400
    sid = body.get("session_id") or str(uuid.uuid4())[:8]

    def generate():
        t0, full = time.time(), []
        try: filtered, docs = _retrieve(q, int(body.get("top_k",5)), float(body.get("min_score",0.1)))
        except Exception as e: yield _sse("error", {"detail": f"Retrieval error: {e}"}); return
        yield _sse("meta", {"session_id": sid, "sources": _sources(docs),
                            "chunks": _chunks_info(filtered), "retrieved_count": len(filtered), "model_used": MODEL_NAME})
        try:
            prompt = _build_prompt(_build_context(docs), q, sid)
            for tok in rag.llm.stream_call(prompt):
                full.append(tok); yield _sse("token", {"token": tok})
        except Exception as e:
            log.exception("Streaming error: %s", e)
            yield _sse("error", {"detail": str(e)}); return
        ans = "".join(full)
        try: add_message(sid, "human", q); add_message(sid, "ai", ans)
        except Exception: pass
        yield _sse("done", {"query_time_ms": round((time.time()-t0)*1000),
                            "answer_found": "I don't have enough information" not in ans})

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# Session endpoints
@query_bp.route("/session/new", methods=["POST"])
def new_session():
    return jsonify(session_id=str(uuid.uuid4())[:8])

@query_bp.route("/session/clear", methods=["POST"])
def clear_session_endpoint():
    body = request.get_json(force=True) or {}
    sid = body.get("session_id", "")
    if not sid: return jsonify(detail="session_id is required."), 400
    return jsonify(cleared=clear_session(sid), session_id=sid)

@query_bp.route("/sessions", methods=["GET"])
def sessions_endpoint():
    return jsonify(sessions=list_sessions())

@query_bp.route("/session/<sid>/history", methods=["GET"])
def session_history_endpoint(sid):
    return jsonify(session_id=sid, messages=get_history(sid, limit=100))

# /api/summarize
@query_bp.route("/summarize", methods=["POST"])
def summarize():
    if not rag.ready: return jsonify(detail="RAG system is still initialising."), 503
    body = request.get_json(force=True) or {}
    source, t0 = body.get("source"), time.time()
    seed = "summary overview introduction main topics key points"
    try:
        kw = {"k": 15, "filter": {"source": source}} if source else {"k": 20}
        results = rag.vectorstore.similarity_search(seed, **kw)
    except Exception as e: return jsonify(detail=f"Retrieval error: {e}"), 500
    if not results: return jsonify(detail="No documents indexed yet."), 404
    try: answer = rag.llm._call(SUMMARIZE_PROMPT_TEMPLATE.format(context=_build_context(results)))
    except Exception as e: return jsonify(detail=str(e)), 502
    return jsonify(answer=answer, answer_found=True, sources=_sources(results), chunks=[],
                   retrieved_count=len(results), query_time_ms=round((time.time()-t0)*1000), model_used=MODEL_NAME)
