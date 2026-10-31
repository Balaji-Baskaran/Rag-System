import pymysql
import pymysql.cursors
from backend import config

def get_conn():
    return pymysql.connect(
        host=config.MYSQL_HOST, port=config.MYSQL_PORT,
        user=config.MYSQL_USER, password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE, autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    try:
        conn = pymysql.connect(
            host=config.MYSQL_HOST, port=config.MYSQL_PORT,
            user=config.MYSQL_USER, password=config.MYSQL_PASSWORD, autocommit=True
        )
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DATABASE}`")
        conn.close()

        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_memory (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(64) NOT NULL,
                    role VARCHAR(16) NOT NULL,
                    content LONGTEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session (session_id)
                )
            """)
        conn.close()
    except Exception as e:
        print(f"[MySQL] Warning during init: {e}")

def save_message(session_id: str, role: str, content: str):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO chat_memory (session_id, role, content) VALUES (%s, %s, %s)",
                        (session_id, role, content))
        conn.close()
    except Exception as e:
        print(f"[MySQL] save_message failed: {e}")

def get_history(session_id: str, limit: int = 6):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT role, content FROM chat_memory WHERE session_id = %s ORDER BY created_at DESC LIMIT %s",
                        (session_id, limit))
            rows = cur.fetchall()
        conn.close()
        return list(reversed(rows))
    except Exception as e:
        print(f"[MySQL] get_history failed: {e}")
        return []

def clear_history(session_id: str):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_memory WHERE session_id = %s", (session_id,))
        conn.close()
    except Exception as e:
        print(f"[MySQL] clear_history failed: {e}")

def list_sessions(limit: int = 30):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT session_id, MAX(created_at) as last_activity,
                       (SELECT content FROM chat_memory m2 
                        WHERE m2.session_id = m1.session_id AND m2.role = 'human' 
                        ORDER BY m2.id ASC LIMIT 1) as title
                FROM chat_memory m1
                GROUP BY session_id
                ORDER BY last_activity DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
        conn.close()
        return [
            {
                "session_id": r["session_id"],
                "title": (r["title"] or "New Chat")[:30],
                "last_activity": str(r["last_activity"])
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[MySQL] list_sessions failed: {e}")
        return []



