import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "ANTHROPIC_API_KEY is missing. Copy .env.example to .env and fill in your key."
    )

SOURCE_DIR = Path(os.environ.get("JOB_SCOUT_SOURCE_DIR", str(Path.home() / "Downloads")))
