import sqlite3

import pytest

from job_scout.analysis import AnalysisResult
from job_scout.db import get_connection, init_db
from job_scout.enrichment import OfferEnrichment, WorkMode
from job_scout.parser import ParsedOffer
from job_scout.storage import save_offer, update_status

OFFER = ParsedOffer(
    title="Software Engineer",
    company="Acme Corp",
    location="",
    url="https://www.linkedin.com/jobs/view/1234",
    description="Build great things.",
)
ENRICHMENT = OfferEnrichment(location="Montreal, QC", work_mode=WorkMode.HYBRID, salary="")
ANALYSIS = AnalysisResult(
    score=7,
    priority=2,
    reasoning="Solid backend fit.",
    points_to_watch=["Confirm salary.", "Confirm contract type."],
    is_duplicate=False,
    duplicate_reference="",
    cv_notes="Use the generalist CV; emphasize the backend API experience.",
)


def _db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return get_connection(db_path)


def test_save_offer_persists_all_fields(tmp_path):
    conn = _db(tmp_path)

    offer_id = save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_Software_Engineer.txt")

    row = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()
    assert row["title"] == "Software Engineer"
    assert row["company"] == "Acme Corp"
    assert row["agency"] is None
    assert row["location"] == "Montreal, QC"
    assert row["url"] == "https://www.linkedin.com/jobs/view/1234"
    assert row["work_mode"] == "hybrid"
    assert row["description"] == "Build great things."
    assert row["source_file"] == "ODE_2026-01-15_Software_Engineer.txt"
    assert row["captured_at"] == "2026-01-15"
    assert row["score"] == 7
    assert row["priority"] == 2
    assert "Solid backend fit." in row["report"]
    assert "Confirm salary." in row["report"]
    assert "Use the generalist CV" in row["report"]
    assert row["status"] == "new"


def test_save_offer_handles_filename_without_date_prefix(tmp_path):
    conn = _db(tmp_path)

    offer_id = save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "not_a_standard_filename.txt")

    row = conn.execute("SELECT captured_at FROM offers WHERE id = ?", (offer_id,)).fetchone()
    assert row["captured_at"] is None


def test_save_offer_rejects_duplicate_source_file(tmp_path):
    conn = _db(tmp_path)
    save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_dup.txt")

    with pytest.raises(sqlite3.IntegrityError):
        save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_dup.txt")


def test_update_status_changes_status_and_timestamp(tmp_path):
    conn = _db(tmp_path)
    offer_id = save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_status.txt")

    update_status(conn, offer_id, "applied")

    row = conn.execute(
        "SELECT status, status_updated_at FROM offers WHERE id = ?", (offer_id,)
    ).fetchone()
    assert row["status"] == "applied"
    assert row["status_updated_at"] is not None


def test_update_status_rejects_invalid_status(tmp_path):
    conn = _db(tmp_path)
    offer_id = save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_status2.txt")

    with pytest.raises(ValueError, match="Invalid status"):
        update_status(conn, offer_id, "not_a_real_status")


def test_update_status_rejects_unknown_offer_id(tmp_path):
    conn = _db(tmp_path)

    with pytest.raises(ValueError, match="No offer with id"):
        update_status(conn, 999, "applied")
