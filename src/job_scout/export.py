import csv
import sqlite3
from pathlib import Path

from job_scout.analysis import compute_action

DEFAULT_EXPORT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "offers_export.csv"
DEFAULT_BRIEF_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "offers_brief.txt"

_COLUMNS = [
    "id",
    "title",
    "company",
    "agency",
    "location",
    "url",
    "work_mode",
    "salary",
    "priority",
    "score",
    "status",
    "captured_at",
    "source_file",
]

_HEADER = [*_COLUMNS, "action"]


def export_to_csv(conn: sqlite3.Connection, output_path: Path = DEFAULT_EXPORT_PATH) -> Path:
    rows = conn.execute(f"SELECT {', '.join(_COLUMNS)} FROM offers ORDER BY id").fetchall()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig (UTF-8 + BOM): plain UTF-8 CSVs open garbled in Excel on
    # Windows for accented characters, which real offer/company names have.
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(_HEADER)
        score_index = _COLUMNS.index("score")
        for row in rows:
            writer.writerow([*row, compute_action(row[score_index])])

    return output_path


def format_offer_report(offer: sqlite3.Row) -> str:
    lines = [
        f"{offer['title']} - {offer['company']}",
        f"Score: {offer['score']}/10 | Priority: {offer['priority']} | "
        f"Action: {compute_action(offer['score'])} | Status: {offer['status']}",
        f"Location: {offer['location'] or 'not specified'} | "
        f"Work mode: {offer['work_mode']} | "
        f"Salary: {offer['salary'] or 'not specified'}",
    ]
    if offer["url"]:
        lines.append(f"URL: {offer['url']}")
    lines.append("")
    lines.append(offer["report"])
    return "\n".join(lines)


def export_brief(offers: list[sqlite3.Row], output_path: Path = DEFAULT_BRIEF_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    separator = f"\n\n{'=' * 80}\n\n"
    with output_path.open("w", encoding="utf-8") as f:
        f.write(separator.join(format_offer_report(offer) for offer in offers))

    return output_path
