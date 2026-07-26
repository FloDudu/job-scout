import csv

from job_scout.analysis import AnalysisResult
from job_scout.db import get_connection, init_db
from job_scout.enrichment import OfferEnrichment, WorkMode
from job_scout.export import export_to_csv
from job_scout.parser import ParsedOffer
from job_scout.storage import save_offer

OFFER = ParsedOffer(
    title="Ingénieur logiciel",
    company="Société Générale",
    location="",
    description="Build great things.",
)
ENRICHMENT = OfferEnrichment(location="Montréal, QC", work_mode=WorkMode.HYBRID, salary="")
ANALYSIS = AnalysisResult(
    score=7,
    priority=2,
    reasoning="Solid backend fit.",
    points_to_watch=["Confirm salary."],
    is_duplicate=False,
    duplicate_reference="",
    cv_notes="Use the generalist CV.",
)


def _db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return get_connection(db_path)


def test_export_writes_all_rows(tmp_path):
    conn = _db(tmp_path)
    save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_a.txt")
    save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-16_b.txt")

    output_path = tmp_path / "export.csv"
    export_to_csv(conn, output_path)

    with output_path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["title"] == "Ingénieur logiciel"
    assert rows[0]["company"] == "Société Générale"
    assert rows[0]["location"] == "Montréal, QC"
    assert rows[0]["score"] == "7"
    assert rows[0]["priority"] == "2"
    assert rows[0]["status"] == "new"


def test_export_excludes_large_text_columns(tmp_path):
    conn = _db(tmp_path)
    save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_c.txt")

    output_path = tmp_path / "export.csv"
    export_to_csv(conn, output_path)

    header = output_path.read_text(encoding="utf-8-sig").splitlines()[0]
    assert "description" not in header
    assert "report" not in header
    assert "embedding" not in header


def test_export_empty_database_writes_header_only(tmp_path):
    conn = _db(tmp_path)

    output_path = tmp_path / "export.csv"
    export_to_csv(conn, output_path)

    with output_path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows == []
