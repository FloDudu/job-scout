from typing import Literal

from pydantic import BaseModel, Field

from job_scout.config import anthropic_client
from job_scout.enrichment import OfferEnrichment
from job_scout.parser import ParsedOffer
from job_scout.profile import profile_system_block
from job_scout.prompt import SimilarOffer, build_analysis_prompt


class AnalysisResult(BaseModel):
    score: int = Field(ge=1, le=10)
    priority: Literal[1, 2]
    reasoning: str
    points_to_watch: list[str]
    is_duplicate: bool
    duplicate_reference: str
    cv_notes: str


def analyze_offer(
    offer: ParsedOffer,
    enrichment: OfferEnrichment,
    similar_offers: list[SimilarOffer] | None = None,
) -> AnalysisResult:
    prompt = build_analysis_prompt(offer, enrichment, similar_offers)

    response = anthropic_client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=2048,
        system=[profile_system_block()],
        messages=[{"role": "user", "content": prompt}],
        output_format=AnalysisResult,
    )
    return response.parsed_output
