import re
from dataclasses import dataclass

_FIELD_PATTERN = re.compile(r"^(TITRE|ENTREPRISE|LOCALISATION|URL):\s*(.*)$")


@dataclass
class ParsedOffer:
    title: str
    company: str
    location: str
    url: str
    description: str


def parse_offer(raw_text: str) -> ParsedOffer:
    header, _, body = raw_text.partition("\nDESCRIPTION:")

    fields: dict[str, str] = {}
    for line in header.splitlines():
        match = _FIELD_PATTERN.match(line)
        if match:
            fields[match.group(1)] = match.group(2).strip()

    return ParsedOffer(
        title=fields.get("TITRE", ""),
        company=fields.get("ENTREPRISE", ""),
        location=fields.get("LOCALISATION", ""),
        url=fields.get("URL", ""),
        description=body.strip(),
    )
