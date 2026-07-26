import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "job_scout.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    agency TEXT,
    location TEXT,
    description TEXT NOT NULL,
    source_file TEXT NOT NULL UNIQUE,
    captured_at TEXT,
    score INTEGER,
    priority INTEGER CHECK (priority IN (1, 2)),
    status TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'applied', 'interview', 'rejected', 'no_response')),
    report TEXT,
    embedding BLOB,
    duplicate_of INTEGER REFERENCES offers(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_updated_at TEXT
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(SCHEMA)
    conn.commit()
    conn.close()
