import csv

from job_scout.analysis import AnalysisResult
from job_scout.db import get_connection, init_db
from job_scout.enrichment import OfferEnrichment, WorkMode
from job_scout.export import export_brief, export_to_csv, format_offer_report
from job_scout.parser import ParsedOffer
from job_scout.storage import get_offer, save_offer

OFFER = ParsedOffer(
    title="Ingénieur logiciel",
    company="Acme Corp",
    location="",
    url="https://www.linkedin.com/jobs/view/1234",
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
    salary_target="80,000-90,000 CAD, a reasoned estimate.",
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
    assert rows[0]["company"] == "Acme Corp"
    assert rows[0]["location"] == "Montréal, QC"
    assert rows[0]["url"] == "https://www.linkedin.com/jobs/view/1234"
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


def test_export_includes_derived_action_column(tmp_path):
    conn = _db(tmp_path)
    save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_d.txt")  # score=7

    output_path = tmp_path / "export.csv"
    export_to_csv(conn, output_path)

    with output_path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["action"] == "Candidature légère"


def test_format_offer_report_includes_header_and_report(tmp_path):
    conn = _db(tmp_path)
    offer_id = save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_e.txt")
    offer = get_offer(conn, offer_id)

    text = format_offer_report(offer)

    assert "Ingénieur logiciel - Acme Corp" in text
    assert "Score: 7/10" in text
    assert "Action: Candidature légère" in text
    assert "https://www.linkedin.com/jobs/view/1234" in text
    assert "80,000-90,000 CAD" in text
    assert "Solid backend fit." in text


def test_export_brief_writes_all_offers_separated(tmp_path):
    conn = _db(tmp_path)
    id_a = save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-15_f.txt")
    id_b = save_offer(conn, OFFER, ENRICHMENT, ANALYSIS, "ODE_2026-01-16_g.txt")
    offers = [get_offer(conn, id_a), get_offer(conn, id_b)]

    output_path = tmp_path / "brief.txt"
    export_brief(offers, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert content.count("Ingénieur logiciel - Acme Corp") == 2
    assert "=" * 80 in content
