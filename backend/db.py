import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("INSIGHTLENS_DB_PATH", "data/insightlens.db"))

def _ensure_data_dir():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    _ensure_data_dir()
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Basic table for ingested items
    c.execute("""
    CREATE TABLE IF NOT EXISTS insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        title TEXT,
        url TEXT,
        content TEXT,
        published_at TEXT,
        inserted_at TEXT DEFAULT (datetime('now')),
        UNIQUE(source, url) ON CONFLICT IGNORE
    );
    """)
    conn.commit()
    conn.close()

def save_insight(source: str, title: str, url: str, content: str, published_at: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO insights (source, title, url, content, published_at)
        VALUES (?, ?, ?, ?, ?);
    """, (source, title or "", url or "", content or "", published_at or ""))
    conn.commit()
    conn.close()
