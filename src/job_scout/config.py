import os
from pathlib import Path

import truststore
from anthropic import Anthropic
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

# Shared client for every module calling the Claude API - single place to
# tune timeout/retries instead of each call site constructing its own.
# max_retries=5 (SDK default: 2) since this runs as an unattended batch job
# where a transient 429/5xx shouldn't fail a whole offer; timeout=60s so one
# stuck request can't stall the batch for the SDK's 10-minute default.
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=5, timeout=60.0)
