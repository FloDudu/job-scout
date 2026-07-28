import pytest

from job_scout.analysis import AnalysisResult, analyze_offer, compute_action
from job_scout.enrichment import OfferEnrichment, WorkMode
from job_scout.parser import ParsedOffer

OFFER = ParsedOffer(
    title="Backend Engineer",
    company="Acme Corp",
    location="",
    url="https://www.linkedin.com/jobs/view/1234",
    description="Build great things.",
)
ENRICHMENT = OfferEnrichment(location="Montreal, QC", work_mode=WorkMode.HYBRID, salary="")


class FakeParsedResponse:
    def __init__(self, parsed_output, stop_reason="end_turn"):
        self.parsed_output = parsed_output
        self.stop_reason = stop_reason


def _analysis(score: int, priority: int) -> AnalysisResult:
    return AnalysisResult(
        score=score,
        priority=priority,
        reasoning="Because.",
        points_to_watch=["Watch this."],
        is_duplicate=False,
        duplicate_reference="",
        cv_notes="Use the right CV.",
        salary_target="80,000-90,000 CAD, a reasoned estimate.",
    )


def test_compute_action_postule_at_8_and_above():
    assert compute_action(8) == "Postule"
    assert compute_action(10) == "Postule"


def test_compute_action_candidature_legere_for_6_and_7():
    assert compute_action(6) == "Candidature légère"
    assert compute_action(7) == "Candidature légère"


def test_compute_action_passe_below_6():
    assert compute_action(5) == "Passe"
    assert compute_action(1) == "Passe"


def test_analyze_offer_caps_score_at_8_for_priority_2(monkeypatch):
    monkeypatch.setattr(
        "job_scout.analysis.anthropic_client.messages.parse",
        lambda **kwargs: FakeParsedResponse(_analysis(score=10, priority=2)),
    )

    result = analyze_offer(OFFER, ENRICHMENT)

    assert result.score == 8


def test_analyze_offer_does_not_cap_priority_1(monkeypatch):
    monkeypatch.setattr(
        "job_scout.analysis.anthropic_client.messages.parse",
        lambda **kwargs: FakeParsedResponse(_analysis(score=10, priority=1)),
    )

    result = analyze_offer(OFFER, ENRICHMENT)

    assert result.score == 10


def test_analyze_offer_raises_when_parsed_output_is_none(monkeypatch):
    monkeypatch.setattr(
        "job_scout.analysis.anthropic_client.messages.parse",
        lambda **kwargs: FakeParsedResponse(None, stop_reason="max_tokens"),
    )

    with pytest.raises(RuntimeError, match="max_tokens"):
        analyze_offer(OFFER, ENRICHMENT)
