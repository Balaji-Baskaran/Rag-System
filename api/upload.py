import logging, threading
from pathlib import Path
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from config import ALLOWED_EXT, UPLOAD_DIR
from rag_core.indexer import index_pdf
from rag_core.state import rag

log = logging.getLogger("studentrag.api.upload")
upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/upload-and-index", methods=["POST"])
def upload_and_index():
    if not rag.ready:
        return jsonify(detail="RAG system is still initialising."), 503
    if "file" not in request.files:
        return jsonify(detail="No file part in request."), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify(detail="No file selected."), 400
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return jsonify(detail=f"Unsupported type '{ext}'. Only PDF accepted."), 400

    filename = secure_filename(file.filename)
    save_path = UPLOAD_DIR / filename
    file.save(str(save_path))
    log.info("Saved: %s (%d bytes)", save_path, save_path.stat().st_size)

    def bg():
        try: log.info("Indexed %d chunks from '%s'", index_pdf(save_path, rag), filename)
        except Exception as e: log.error("Indexing failed '%s': %s", filename, e, exc_info=True)
    threading.Thread(target=bg, name=f"index-{filename}", daemon=True).start()

    return jsonify(message=f"'{filename}' uploaded. Indexing in background.", filename=filename), 202
