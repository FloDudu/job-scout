import pytest

from job_scout import profile


def test_load_profile_raises_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(profile, "PROFILE_PATH", tmp_path / "missing_profile.md")

    with pytest.raises(RuntimeError, match="Profile not found"):
        profile.load_profile()


def test_load_profile_returns_file_content(tmp_path, monkeypatch):
    profile_path = tmp_path / "profile.md"
    profile_path.write_text("# My profile\nPriority 1: AI/ML.", encoding="utf-8")
    monkeypatch.setattr(profile, "PROFILE_PATH", profile_path)

    assert profile.load_profile() == "# My profile\nPriority 1: AI/ML."


def test_profile_system_block_wraps_content_with_cache_control(tmp_path, monkeypatch):
    profile_path = tmp_path / "profile.md"
    profile_path.write_text("Some profile content.", encoding="utf-8")
    monkeypatch.setattr(profile, "PROFILE_PATH", profile_path)

    block = profile.profile_system_block()

    assert block == {
        "type": "text",
        "text": "Some profile content.",
        "cache_control": {"type": "ephemeral"},
    }
