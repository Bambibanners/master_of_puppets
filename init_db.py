import sqlite3
import os

DB_NAME = "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    guid TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'ASSIGNED', 'RUNNING', 'COMPLETED', 'FAILED')),
    priority INTEGER DEFAULT 0,
    payload TEXT NOT NULL,
    result TEXT,
    error_details TEXT,
    node_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    lineage_log TEXT
);

CREATE TABLE IF NOT EXISTS semaphores (
    resource_key TEXT PRIMARY KEY,
    capacity INTEGER NOT NULL,
    current_usage INTEGER DEFAULT 0
);
"""

def init_db():
    if os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} already exists.")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.executescript(SCHEMA)
        conn.commit()
        print(f"Schema initialized in {DB_NAME}")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
