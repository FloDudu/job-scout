from job_scout.enrichment import OfferEnrichment, WorkMode
from job_scout.parser import ParsedOffer
from job_scout.prompt import SimilarOffer, build_analysis_prompt

OFFER = ParsedOffer(
    title="Software Engineer",
    company="Acme Corp",
    location="",
    url="https://www.linkedin.com/jobs/view/1234",
    description="Build great things.",
)


def test_includes_offer_fields():
    enrichment = OfferEnrichment(
        location="Montreal, QC", work_mode=WorkMode.HYBRID, salary="90000-110000 CAD/year"
    )

    prompt = build_analysis_prompt(OFFER, enrichment)

    assert "Software Engineer" in prompt
    assert "Acme Corp" in prompt
    assert "Montreal, QC" in prompt
    assert "hybrid" in prompt
    assert "90000-110000 CAD/year" in prompt
    assert "Build great things." in prompt


def test_missing_location_and_salary_fall_back_to_not_specified():
    enrichment = OfferEnrichment(location="", work_mode=WorkMode.UNKNOWN, salary="")

    prompt = build_analysis_prompt(OFFER, enrichment)

    assert "Location: not specified" in prompt
    assert "Salary: not specified" in prompt


def test_no_similar_offers_by_default():
    enrichment = OfferEnrichment(location="", work_mode=WorkMode.UNKNOWN, salary="")

    prompt = build_analysis_prompt(OFFER, enrichment)

    assert "None found in the database." in prompt


def test_similar_offers_are_listed():
    enrichment = OfferEnrichment(location="", work_mode=WorkMode.UNKNOWN, salary="")
    similar = [
        SimilarOffer(
            title="Software Engineer",
            company="Acme Corp",
            agency="RecruitCo",
            status="rejected",
            score=6,
        )
    ]

    prompt = build_analysis_prompt(OFFER, enrichment, similar_offers=similar)

    assert "RecruitCo" in prompt
    assert "rejected" in prompt
    assert "None found in the database." not in prompt


def test_instructions_mention_dual_priority_and_constraints():
    enrichment = OfferEnrichment(location="", work_mode=WorkMode.UNKNOWN, salary="")

    prompt = build_analysis_prompt(OFFER, enrichment)

    assert "priority 1" in prompt
    assert "priority 2" in prompt
    assert "non-negotiable constraints" in prompt
    assert "CV tailoring notes" in prompt
