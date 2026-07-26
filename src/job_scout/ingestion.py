import shutil
from pathlib import Path

from job_scout.config import SOURCE_DIR


def find_offer_files(source_dir: Path = SOURCE_DIR) -> list[Path]:
    """ODE_*.txt files still present in the watched folder.

    A file moved to ODE_processed/ or ODE_errors/ no longer matches this
    glob - that's what tracks already-processed files, rather than a
    separate state column in the DB.
    """
    return sorted(source_dir.glob("ODE_*.txt"))


def read_offer_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _unique_destination(target_dir: Path, name: str) -> Path:
    destination = target_dir / name
    if not destination.exists():
        return destination

    stem, suffix = Path(name).stem, Path(name).suffix
    counter = 1
    while destination.exists():
        destination = target_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    return destination


def _move_to(path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(target_dir, path.name)
    shutil.move(str(path), str(destination))
    return destination


def move_to_processed(path: Path, source_dir: Path = SOURCE_DIR) -> Path:
    return _move_to(path, source_dir / "ODE_processed")


def move_to_errors(path: Path, source_dir: Path = SOURCE_DIR) -> Path:
    return _move_to(path, source_dir / "ODE_errors")
