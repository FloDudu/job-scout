from typing import Literal

from job_scout.config import anthropic_client
from job_scout.profile import profile_system_block

_LANGUAGE_NAMES = {"fr": "French", "en": "English"}

_PROMPT_TEMPLATE = """Write a cover letter in {language_name} for the following job offer, \
based on my profile (given above as context) and the analysis already done for this offer.

Offer:
Title: {title}
Company: {company}

Description:
{description}

Prior analysis of this offer:
{report}

Rules:
- Write only the cover letter body - no subject line, no placeholder brackets like
  [Company Name] (use the real company name given above), just a natural opening and
  closing.
- Ground every claim in my actual profile - do not invent experience, metrics, or
  projects that aren't in it.
- Keep it concise: 3-4 short paragraphs, not a full page.
- Reflect the CV tailoring notes from the prior analysis (what to emphasize) rather
  than repeating the whole CV.
"""


def generate_cover_letter(
    title: str,
    company: str,
    description: str,
    report: str,
    language: Literal["fr", "en"],
) -> str:
    prompt = _PROMPT_TEMPLATE.format(
        language_name=_LANGUAGE_NAMES[language],
        title=title,
        company=company,
        description=description,
        report=report,
    )

    response = anthropic_client.messages.create(
        model="claude-sonnet-5",
        max_tokens=2048,
        system=[profile_system_block()],
        messages=[{"role": "user", "content": prompt}],
    )
    return next(block.text for block in response.content if block.type == "text")
