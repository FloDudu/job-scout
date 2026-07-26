import pytest

import job_scout.dedup as dedup
from job_scout.analysis import AnalysisResult
from job_scout.db import get_connection, init_db
from job_scout.dedup import content_hash, embed_text, find_hash_duplicates, normalize_text
from job_scout.enrichment import OfferEnrichment, WorkMode
from job_scout.parser import ParsedOffer
from job_scout.storage import save_offer

OFFER = ParsedOffer(
    title="Software Engineer",
    company="Acme Corp",
    location="",
    description="We are looking for a Software Engineer to join our team.",
)
ENRICHMENT = OfferEnrichment(location="Montreal, QC", work_mode=WorkMode.HYBRID, salary="")
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


def test_normalize_text_collapses_whitespace_and_case():
    a = normalize_text("  Hello   World  \n\n  ")
    b = normalize_text("hello world")
    assert a == b == "hello world"


def test_content_hash_is_stable_and_case_insensitive():
    assert content_hash("Hello World") == content_hash("hello   world")


def test_content_hash_differs_for_different_text():
    assert content_hash("Software Engineer role") != content_hash("Data Scientist role")


def test_find_hash_duplicates_empty_when_nothing_stored(tmp_path):
    conn = _db(tmp_path)

    assert find_hash_duplicates(conn, "Some description text.") == []


def test_find_hash_duplicates_matches_identical_description(tmp_path):
    conn = _db(tmp_path)
    save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_a.txt")

    duplicates = find_hash_duplicates(conn, OFFER.description)

    assert len(duplicates) == 1
    assert duplicates[0].title == "Software Engineer"
    assert duplicates[0].company == "Acme Corp"
    assert duplicates[0].status == "new"
    assert duplicates[0].score == 7


def test_find_hash_duplicates_matches_despite_whitespace_case_differences(tmp_path):
    conn = _db(tmp_path)
    save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_b.txt")

    reworded_whitespace = OFFER.description.upper().replace(" ", "  ")
    duplicates = find_hash_duplicates(conn, reworded_whitespace)

    assert len(duplicates) == 1


def test_find_hash_duplicates_no_match_for_different_description(tmp_path):
    conn = _db(tmp_path)
    save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_c.txt")

    assert find_hash_duplicates(conn, "A completely unrelated job posting.") == []


def test_embed_text_raises_clear_error_without_voyage_key(monkeypatch):
    monkeypatch.setattr(dedup, "VOYAGE_API_KEY", None)
    monkeypatch.setattr(dedup, "_voyage_client", None)

    with pytest.raises(RuntimeError, match="VOYAGE_API_KEY is missing"):
        embed_text("some text")
