import os
from pathlib import Path

import truststore
from dotenv import load_dotenv

# Use the OS certificate store instead of certifi's bundle - needed on
# machines where a corporate proxy/antivirus injects its own root CA
# (otherwise every HTTPS call in the project fails with
# CERTIFICATE_VERIFY_FAILED). Must run before any HTTP client is built.
truststore.inject_into_ssl()

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "ANTHROPIC_API_KEY is missing. Copy .env.example to .env and fill in your key."
    )

SOURCE_DIR = Path(os.environ.get("JOB_SCOUT_SOURCE_DIR", str(Path.home() / "Downloads")))
