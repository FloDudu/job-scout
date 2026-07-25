import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "job_scout.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS offres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    entreprise TEXT,
    agence TEXT,
    localisation TEXT,
    description TEXT NOT NULL,
    fichier_source TEXT NOT NULL UNIQUE,
    date_captation TEXT,
    score INTEGER,
    priorite INTEGER CHECK (priorite IN (1, 2)),
    statut TEXT NOT NULL DEFAULT 'nouveau'
        CHECK (statut IN ('nouveau', 'postule', 'entretien', 'refuse', 'sans_suite')),
    rapport TEXT,
    embedding BLOB,
    doublon_de INTEGER REFERENCES offres(id),
    date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_maj_statut TEXT
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
