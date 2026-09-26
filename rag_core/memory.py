import logging
from collections import defaultdict
import pymysql, pymysql.cursors
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MEMORY_MAX_MESSAGES

log = logging.getLogger("studentrag.memory")
_fallback = defaultdict(list)

_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS chat_memory (
        id INT AUTO_INCREMENT PRIMARY KEY, session_id VARCHAR(64) NOT NULL,
        role VARCHAR(16) NOT NULL, content LONGTEXT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_session (session_id), INDEX idx_session_time (session_id, created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS chat_sessions (
        session_id VARCHAR(64) PRIMARY KEY,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_used_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
]

def _conn():
    return pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DATABASE, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=True, connect_timeout=3)

def init_memory_tables():
    try:
        conn = _conn()
        with conn.cursor() as cur:
            for sql in _SCHEMA: cur.execute(sql)
        conn.close()
        log.info("MySQL memory tables ready")
    except Exception as e:
        log.warning("MySQL unavailable, using in-memory session fallback: %s", e)

def add_message(session_id, role, content):
    try:
        conn = _conn()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO chat_memory (session_id,role,content) VALUES (%s,%s,%s)",
                            (session_id, role, content))
                cur.execute("INSERT INTO chat_sessions (session_id,last_used_at) VALUES (%s,NOW()) "
                            "ON DUPLICATE KEY UPDATE last_used_at=NOW()", (session_id,))
        finally:
            conn.close()
    except Exception:
        _fallback[session_id].append({"role": role, "content": content})

def get_history(session_id, limit=None):
    try:
        conn = _conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT role,content FROM chat_memory WHERE session_id=%s "
                            "ORDER BY created_at DESC LIMIT %s", (session_id, limit or MEMORY_MAX_MESSAGES))
                return list(reversed(cur.fetchall()))
        finally:
            conn.close()
    except Exception:
        return _fallback.get(session_id, [])[-(limit or MEMORY_MAX_MESSAGES):]

def clear_session(session_id):
    _fallback.pop(session_id, None)
    try:
        conn = _conn()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chat_memory WHERE session_id=%s", (session_id,))
                d = cur.rowcount
                cur.execute("DELETE FROM chat_sessions WHERE session_id=%s", (session_id,))
            return d
        finally:
            conn.close()
    except Exception:
        return 0

def format_history_for_prompt(history):
    return "\n".join(f"{'Student' if m['role']=='human' else 'Assistant'}: {m['content']}" for m in history) if history else ""

def list_sessions(limit=30):
    try:
        conn = _conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT s.session_id, s.last_used_at,
                           (SELECT content FROM chat_memory m 
                            WHERE m.session_id = s.session_id AND m.role = 'human' 
                            ORDER BY m.created_at ASC LIMIT 1) AS title
                    FROM chat_sessions s
                    ORDER BY s.last_used_at DESC
                    LIMIT %s
                """, (limit,))
                sessions = []
                for r in cur.fetchall():
                    t = (r.get("title") or "").strip()
                    if not t: continue
                    if len(t) > 32: t = t[:30] + "..."
                    sessions.append({"session_id": r["session_id"], "title": t})
                return sessions
        finally:
            conn.close()
    except Exception:
        sessions = []
        for sid, msgs in reversed(list(_fallback.items())):
            for m in msgs:
                if m.get("role") == "human":
                    t = m["content"][:30] + ("..." if len(m["content"]) > 30 else "")
                    sessions.append({"session_id": sid, "title": t})
                    break
        return sessions[:limit]
