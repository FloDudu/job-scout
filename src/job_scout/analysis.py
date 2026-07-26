from typing import Literal

from anthropic import Anthropic
from pydantic import BaseModel, Field

from job_scout.config import ANTHROPIC_API_KEY
from job_scout.enrichment import OfferEnrichment
from job_scout.parser import ParsedOffer
from job_scout.profile import profile_system_block
from job_scout.prompt import SimilarOffer, build_analysis_prompt

_client = Anthropic(api_key=ANTHROPIC_API_KEY)


class AnalysisResult(BaseModel):
    score: int = Field(ge=1, le=10)
    priority: Literal[1, 2]
    reasoning: str
    points_to_watch: list[str]
    is_duplicate: bool
    duplicate_reference: str


def analyze_offer(
    offer: ParsedOffer,
    enrichment: OfferEnrichment,
    similar_offers: list[SimilarOffer] | None = None,
) -> AnalysisResult:
    prompt = build_analysis_prompt(offer, enrichment, similar_offers)

    response = _client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=2048,
        system=[profile_system_block()],
        messages=[{"role": "user", "content": prompt}],
        output_format=AnalysisResult,
    )
    return response.parsed_output
