from enum import Enum

from pydantic import BaseModel

from job_scout.config import anthropic_client

_PROMPT_TEMPLATE = """Extract the job's location, work mode, and posted salary from \
the description below.

Rules:
- location: the city/region/country the role is based in, as mentioned (e.g. \
"Montreal, QC", "New York, NY"). Empty string if no base location is mentioned at all.
- work_mode: one of
  - "onsite": the description explicitly requires on-site presence with no \
remote/hybrid option mentioned.
  - "hybrid": a mix of on-site and remote/work-from-home is mentioned (any language, \
including "teletravail partiel").
  - "remote": the role is fully remote, no on-site requirement.
  - "unknown": the description says nothing about the work arrangement at all.
- salary: the salary/compensation as stated in the description, verbatim or lightly \
normalized (e.g. "90000-110000 CAD/year", "$45/hour"). Empty string if no salary or \
compensation figure is mentioned at all. Do not estimate or infer a figure that isn't \
explicitly stated.

Description:
{description}
"""


class WorkMode(str, Enum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
    UNKNOWN = "unknown"


class OfferEnrichment(BaseModel):
    location: str
    work_mode: WorkMode
    salary: str


def enrich_offer(description: str) -> OfferEnrichment:
    response = anthropic_client.messages.parse(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": _PROMPT_TEMPLATE.format(description=description)}],
        output_format=OfferEnrichment,
    )
    if response.parsed_output is None:
        raise RuntimeError(
            f"Enrichment returned no parsed output (stop_reason={response.stop_reason!r})"
        )
    return response.parsed_output
