from dataclasses import dataclass

from job_scout.enrichment import OfferEnrichment
from job_scout.parser import ParsedOffer


@dataclass
class SimilarOffer:
    title: str
    company: str
    agency: str
    status: str
    score: int | None


def _format_similar_offers(similar_offers: list[SimilarOffer]) -> str:
    if not similar_offers:
        return "None found in the database."
    return "\n".join(
        f"- {s.title!r} at {s.company} (posted by {s.agency}), "
        f"status: {s.status}, previous score: {s.score}"
        for s in similar_offers
    )


def build_analysis_prompt(
    offer: ParsedOffer,
    enrichment: OfferEnrichment,
    similar_offers: list[SimilarOffer] | None = None,
) -> str:
    similar_offers = similar_offers or []

    return f"""Evaluate this job offer against my profile (given above as context).

Rules:
- State explicitly whether this offer matches priority 1 (AI/ML) or priority 2
  (general/backend) from my profile.
- Check it against my non-negotiable constraints (location/remote, salary
  floor, legal status, languages) and flag any violation clearly.
- If similar offers are listed below, treat this as a likely repost by a
  different agency - say so and reference what I already know about it
  (status, previous score). Never silently skip it; flag it so I can decide.
- List concrete points to watch before applying (e.g. vague requirements,
  contract type, red flags in the description).

Offer:
Title: {offer.title}
Company: {offer.company}
Location: {enrichment.location or "not specified"}
Work mode: {enrichment.work_mode.value}
Salary: {enrichment.salary or "not specified"}

Description:
{offer.description}

Similar offers already seen:
{_format_similar_offers(similar_offers)}
"""
