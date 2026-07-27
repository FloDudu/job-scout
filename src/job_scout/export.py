import csv
import sqlite3
from pathlib import Path

DEFAULT_EXPORT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "offers_export.csv"

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


def export_to_csv(conn: sqlite3.Connection, output_path: Path = DEFAULT_EXPORT_PATH) -> Path:
    rows = conn.execute(f"SELECT {', '.join(_COLUMNS)} FROM offers ORDER BY id").fetchall()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig (UTF-8 + BOM): plain UTF-8 CSVs open garbled in Excel on
    # Windows for accented characters, which real offer/company names have.
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(_COLUMNS)
        writer.writerows(rows)

    return output_path
