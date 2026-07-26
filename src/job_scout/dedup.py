import hashlib
import re
import sqlite3

import numpy as np
import voyageai

from job_scout.config import VOYAGE_API_KEY
from job_scout.prompt import SimilarOffer

_EMBEDDING_MODEL = "voyage-3"
_voyage_client: voyageai.Client | None = None


def _get_voyage_client() -> voyageai.Client:
    global _voyage_client
    if not VOYAGE_API_KEY:
        raise RuntimeError(
            "VOYAGE_API_KEY is missing. Add it to .env to enable duplicate detection."
        )
    if _voyage_client is None:
        _voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)
    return _voyage_client


def embed_text(text: str) -> np.ndarray:
    result = _get_voyage_client().embed([text], model=_EMBEDDING_MODEL, input_type="document")
    return np.array(result.embeddings[0], dtype=np.float32)


def serialize_embedding(embedding: np.ndarray) -> bytes:
    return embedding.astype(np.float32).tobytes()


def deserialize_embedding(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def content_hash(description: str) -> str:
    return hashlib.sha256(normalize_text(description).encode("utf-8")).hexdigest()


# Starting point, not yet validated against real repost data - see #12.
DEFAULT_SIMILARITY_THRESHOLD = 0.85


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


def find_similar_by_embedding(
    conn: sqlite3.Connection,
    embedding: np.ndarray,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    exclude_id: int | None = None,
) -> list[SimilarOffer]:
    """Second-tier dedup: cosine similarity against every stored embedding.

    Only meant to run on offers that already passed the hash filter (#9)
    without a match - catches reworded reposts the hash tier can't see.
    Fetches every row with an embedding rather than using a vector index:
    at personal-tool scale (tens to low hundreds of offers) a linear scan
    in Python is simpler and fast enough.
    """
    rows = conn.execute(
        "SELECT id, title, company, agency, status, score, embedding "
        "FROM offers WHERE embedding IS NOT NULL"
    ).fetchall()

    similar = []
    for row in rows:
        if exclude_id is not None and row["id"] == exclude_id:
            continue
        stored_embedding = deserialize_embedding(row["embedding"])
        if cosine_similarity(embedding, stored_embedding) >= threshold:
            similar.append(
                SimilarOffer(
                    title=row["title"],
                    company=row["company"] or "",
                    agency=row["agency"] or "",
                    status=row["status"],
                    score=row["score"],
                )
            )
    return similar
