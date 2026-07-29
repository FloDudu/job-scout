import re
import sqlite3

import numpy as np

from job_scout.analysis import AnalysisResult
from job_scout.dedup import content_hash, serialize_embedding
from job_scout.enrichment import OfferEnrichment
from job_scout.parser import ParsedOffer

_DATE_PATTERN = re.compile(r"ODE_(\d{4}-\d{2}-\d{2})_")

# Must match the CHECK constraint on offers.status in db.py's SCHEMA.
VALID_STATUSES = {"new", "applied", "interview", "rejected", "no_response"}


def _captured_at_from_filename(source_file: str) -> str | None:
    match = _DATE_PATTERN.match(source_file)
    return match.group(1) if match else None


def _format_report(analysis: AnalysisResult) -> str:
    points = "\n".join(f"- {p}" for p in analysis.points_to_watch)
    return (
        f"{analysis.reasoning}\n\n"
        f"Points to watch:\n{points}\n\n"
        f"Salary target: {analysis.salary_target}\n\n"
        f"CV notes:\n{analysis.cv_notes}"
    )


def save_offer(
    conn: sqlite3.Connection,
    offer: ParsedOffer,
    enrichment: OfferEnrichment,
    analysis: AnalysisResult,
    source_file: str,
    embedding: np.ndarray | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO offers (
            title, company, location, url, work_mode, salary, description,
            source_file, captured_at, score, priority, report, content_hash,
            embedding
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            offer.title,
            offer.company,
            enrichment.location,
            offer.url,
            enrichment.work_mode.value,
            enrichment.salary,
            offer.description,
            source_file,
            _captured_at_from_filename(source_file),
            analysis.score,
            analysis.priority,
            _format_report(analysis),
            content_hash(offer.description),
            serialize_embedding(embedding) if embedding is not None else None,
        ),
    )
    conn.commit()
    assert cursor.lastrowid is not None  # always set after a successful INSERT
    return cursor.lastrowid


def get_offer(conn: sqlite3.Connection, offer_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()


def list_offers(
    conn: sqlite3.Connection, date: str | None = None, status: str | None = None
) -> list[sqlite3.Row]:
    query = "SELECT id, title, company, score, priority, status FROM offers"
    conditions = []
    params: list[str] = []
    if date is not None:
        conditions.append("captured_at = ?")
        params.append(date)
    if status is not None:
        conditions.append("status = ?")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY score DESC, id"
    return conn.execute(query, params).fetchall()


def update_status(conn: sqlite3.Connection, offer_id: int, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status {status!r}. Must be one of {sorted(VALID_STATUSES)}.")

    cursor = conn.execute(
        "UPDATE offers SET status = ?, status_updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, offer_id),
    )
    conn.commit()

    if cursor.rowcount == 0:
        raise ValueError(f"No offer with id {offer_id}.")
