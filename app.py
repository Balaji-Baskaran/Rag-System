import logging
from flask import Flask, render_template
from flask_cors import CORS
from config import BASE_DIR, configure_logging
from rag_core.state import start_rag_init
from rag_core.memory import init_memory_tables
from api.health import health_bp
from api.query  import query_bp
from api.upload import upload_bp

def create_app():
    configure_logging()
    app = Flask(__name__,
        static_folder=str(BASE_DIR / "frontend" / "static"),
        template_folder=str(BASE_DIR / "frontend" / "templates"))
    CORS(app)

    for bp, prefix in [(health_bp, "/api"), (query_bp, "/api"), (upload_bp, "/api")]:
        app.register_blueprint(bp, url_prefix=prefix)

    @app.route("/")
    def index():
        return render_template("index.html")

    try:
        init_memory_tables()
    except Exception as exc:
        logging.getLogger("studentrag").warning("MySQL memory init failed: %s", exc)

    start_rag_init()
    return app

application = create_app()
if __name__ == "__main__":
    application.run(debug=False, host="0.0.0.0", port=5000, use_reloader=False)