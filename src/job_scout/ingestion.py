from pathlib import Path

from job_scout.config import SOURCE_DIR


def find_offer_files(source_dir: Path = SOURCE_DIR) -> list[Path]:
    """ODE_*.txt files still present in the watched folder.

    A file moved to ODE_processed/ or ODE_errors/ (ticket #6) no longer
    matches this glob - that's what tracks already-processed files,
    rather than a separate state column in the DB.
    """
    return sorted(source_dir.glob("ODE_*.txt"))


def read_offer_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")
