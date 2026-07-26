import re
import sqlite3

from job_scout.analysis import AnalysisResult
from job_scout.enrichment import OfferEnrichment
from job_scout.parser import ParsedOffer

_DATE_PATTERN = re.compile(r"ODE_(\d{4}-\d{2}-\d{2})_")


def _captured_at_from_filename(source_file: str) -> str | None:
    match = _DATE_PATTERN.match(source_file)
    return match.group(1) if match else None


def _format_report(analysis: AnalysisResult) -> str:
    points = "\n".join(f"- {p}" for p in analysis.points_to_watch)
    return f"{analysis.reasoning}\n\nPoints to watch:\n{points}"


def save_offer(
    conn: sqlite3.Connection,
    offer: ParsedOffer,
    enrichment: OfferEnrichment,
    analysis: AnalysisResult,
    source_file: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO offers (
            title, company, location, work_mode, salary, description,
            source_file, captured_at, score, priority, report
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            offer.title,
            offer.company,
            enrichment.location,
            enrichment.work_mode.value,
            enrichment.salary,
            offer.description,
            source_file,
            _captured_at_from_filename(source_file),
            analysis.score,
            analysis.priority,
            _format_report(analysis),
        ),
    )
    conn.commit()
    return cursor.lastrowid
