import hashlib
import re
import sqlite3

from job_scout.prompt import SimilarOffer


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def content_hash(description: str) -> str:
    return hashlib.sha256(normalize_text(description).encode("utf-8")).hexdigest()


def find_hash_duplicates(conn: sqlite3.Connection, description: str) -> list[SimilarOffer]:
    """Cheap first-tier dedup: exact match on normalized description text.

    Catches identical/near-identical reposts (whitespace/case differences
    only) without spending an embedding call. Reworded reposts fall through
    to the embedding-based similarity search instead.
    """
    rows = conn.execute(
        "SELECT title, company, agency, status, score FROM offers WHERE content_hash = ?",
        (content_hash(description),),
    ).fetchall()
    return [
        SimilarOffer(
            title=row["title"],
            company=row["company"] or "",
            agency=row["agency"] or "",
            status=row["status"],
            score=row["score"],
        )
        for row in rows
    ]
