import pymysql, sys
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS chat_memory (
        id INT AUTO_INCREMENT PRIMARY KEY, session_id VARCHAR(64) NOT NULL,
        role VARCHAR(16) NOT NULL, content LONGTEXT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_session (session_id), INDEX idx_session_time (session_id, created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS chat_sessions (
        session_id VARCHAR(64) PRIMARY KEY, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_used_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
]

def main():
    print("Initializing database...")
    try:
        conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                               password=MYSQL_PASSWORD, charset="utf8mb4", autocommit=True)
    except pymysql.err.OperationalError:
        print("Database server connection failed. Please ensure MySQL is running.")
        sys.exit(1)
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.execute(f"USE `{MYSQL_DATABASE}`")
        for sql in _SCHEMA: cur.execute(sql)
    conn.close()
    print("Database ready.")

if __name__ == "__main__":
    main()
