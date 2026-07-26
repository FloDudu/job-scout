from anthropic import Anthropic
from pydantic import BaseModel

from job_scout.config import ANTHROPIC_API_KEY

_client = Anthropic(api_key=ANTHROPIC_API_KEY)

_PROMPT_TEMPLATE = """Extract the job's geographic location from the description below.

Rules:
- Return the city/region/country as mentioned (e.g. "Montreal, QC", "Remote", "New York, NY (Hybrid)").
- If several locations are mentioned, return the primary one.
- If no location is mentioned anywhere in the text, return an empty string.

Description:
{description}
"""


class LocationExtraction(BaseModel):
    location: str


def extract_location(description: str) -> str:
    response = _client.messages.parse(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[
            {"role": "user", "content": _PROMPT_TEMPLATE.format(description=description)}
        ],
        output_format=LocationExtraction,
    )
    return response.parsed_output.location
