import pytest

from job_scout import cli
from job_scout.analysis import AnalysisResult
from job_scout.db import get_connection, init_db
from job_scout.enrichment import OfferEnrichment, WorkMode
from job_scout.parser import ParsedOffer
from job_scout.storage import save_offer

OFFER = ParsedOffer(
    title="Backend Engineer",
    company="Acme Corp",
    location="",
    url="https://www.linkedin.com/jobs/view/1234",
    description="Build great things.",
)
ENRICHMENT = OfferEnrichment(location="Montreal, QC", work_mode=WorkMode.HYBRID, salary="")


def _analysis(score: int, priority: int = 2) -> AnalysisResult:
    return AnalysisResult(
        score=score,
        priority=priority,
        reasoning="Because.",
        points_to_watch=["Watch this."],
        is_duplicate=False,
        duplicate_reference="",
        cv_notes="Use the right CV.",
    )


@pytest.fixture
def db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    monkeypatch.setattr(cli, "get_connection", lambda: get_connection(db_path))
    return db_path


def test_cmd_show_unknown_id_raises_system_exit(db):
    with pytest.raises(SystemExit, match="No offer with id 999"):
        cli.cmd_show(999)


def test_cmd_show_prints_the_full_report(db, capsys):
    conn = get_connection(db)
    save_offer(conn, OFFER, ENRICHMENT, _analysis(8, priority=1), "ODE_2026-01-15_a.txt")
    conn.close()

    cli.cmd_show(1)

    out = capsys.readouterr().out
    assert "Backend Engineer - Acme Corp" in out
    assert "Action: Postule" in out
    assert "Because." in out


def test_cmd_status_unknown_id_raises_system_exit(db):
    with pytest.raises(SystemExit, match="No offer with id 999"):
        cli.cmd_status(999, "applied")


def test_cmd_status_updates_and_prints_confirmation(db, capsys):
    conn = get_connection(db)
    save_offer(conn, OFFER, ENRICHMENT, _analysis(5), "ODE_2026-01-15_a.txt")
    conn.close()

    cli.cmd_status(1, "applied")

    assert "Offer 1 -> applied" in capsys.readouterr().out


def test_cmd_letter_unknown_id_raises_system_exit(db):
    with pytest.raises(SystemExit, match="No offer with id 999"):
        cli.cmd_letter(999, "en")


def test_cmd_list_no_matching_offers(db, capsys):
    cli.cmd_list(None, False)

    assert "No matching offers." in capsys.readouterr().out


def test_cmd_list_actionable_filters_out_passe(db, capsys):
    conn = get_connection(db)
    save_offer(conn, OFFER, ENRICHMENT, _analysis(4), "ODE_2026-01-15_low.txt")
    save_offer(conn, OFFER, ENRICHMENT, _analysis(6), "ODE_2026-01-15_mid.txt")
    save_offer(conn, OFFER, ENRICHMENT, _analysis(8, priority=1), "ODE_2026-01-15_high.txt")
    conn.close()

    cli.cmd_list(None, True)

    lines = [line for line in capsys.readouterr().out.splitlines()[1:] if line]
    assert len(lines) == 2
    assert all("Passe" not in line for line in lines)


def test_cmd_list_date_filters(db, capsys):
    conn = get_connection(db)
    save_offer(conn, OFFER, ENRICHMENT, _analysis(5), "ODE_2026-01-15_a.txt")
    save_offer(conn, OFFER, ENRICHMENT, _analysis(5), "ODE_2026-01-16_b.txt")
    conn.close()

    cli.cmd_list("2026-01-15", False)

    lines = [line for line in capsys.readouterr().out.splitlines()[1:] if line]
    assert len(lines) == 1


def test_cmd_brief_no_matching_offers(db, tmp_path, capsys):
    output_path = tmp_path / "brief.txt"

    cli.cmd_brief(None, False, output_path)

    assert "No matching offers." in capsys.readouterr().out
    assert not output_path.exists()


def test_cmd_brief_writes_filtered_offers(db, tmp_path, capsys):
    conn = get_connection(db)
    save_offer(conn, OFFER, ENRICHMENT, _analysis(4), "ODE_2026-01-15_low.txt")
    save_offer(conn, OFFER, ENRICHMENT, _analysis(8, priority=1), "ODE_2026-01-15_high.txt")
    conn.close()

    output_path = tmp_path / "brief.txt"
    cli.cmd_brief(None, True, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert content.count("Backend Engineer - Acme Corp") == 1
    assert "Action: Postule" in content
    assert "Wrote 1 offer(s)" in capsys.readouterr().out
