from pathlib import Path

PROFILE_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "profile.md"


def load_profile() -> str:
    if not PROFILE_PATH.exists():
        raise RuntimeError(
            f"Profile not found at {PROFILE_PATH}. "
            "Write your CV/criteria into config/profile.md (see ticket #13)."
        )
    return PROFILE_PATH.read_text(encoding="utf-8")


def profile_system_block() -> dict:
    return {
        "type": "text",
        "text": load_profile(),
        "cache_control": {"type": "ephemeral"},
    }
