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
    salary_target: str


def analyze_offer(
    offer: ParsedOffer,
    enrichment: OfferEnrichment,
    similar_offers: list[SimilarOffer] | None = None,
) -> AnalysisResult:
    prompt = build_analysis_prompt(offer, enrichment, similar_offers)

    # 2048 proved too low in real use: reasoning + points_to_watch + cv_notes
    # can run long on detailed offers, and a response cut off mid-JSON fails
    # Pydantic parsing entirely (not just truncates a field).
    response = anthropic_client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=8192,
        system=[profile_system_block()],
        messages=[{"role": "user", "content": prompt}],
        output_format=AnalysisResult,
    )

    if response.parsed_output is None:
        raise RuntimeError(
            f"Analysis returned no parsed output (stop_reason={response.stop_reason!r})"
        )

    result = response.parsed_output
    # Priority 1 (AI/ML, the actual goal) must always outrank priority 2
    # (generalist fallback) on raw score - enforced here rather than left
    # to the prompt, since a numeric ceiling is a deterministic business
    # rule, not something to trust the model to self-apply.
    if result.priority == 2:
        result.score = min(result.score, 8)
    return result


def compute_action(score: int) -> str:
    if score >= 8:
        return "Postule"
    if score >= 6:
        return "Candidature légère"
    return "Passe"
