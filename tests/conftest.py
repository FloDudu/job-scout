import pytest

from job_scout import profile


@pytest.fixture(autouse=True)
def fake_profile(tmp_path, monkeypatch):
    # analyze_offer()/generate_cover_letter() pull the candidate profile in
    # as a system block - without this they'd hit the real (gitignored)
    # config/profile.md, which doesn't exist in CI.
    profile_path = tmp_path / "profile.md"
    profile_path.write_text("Fake profile content.", encoding="utf-8")
    monkeypatch.setattr(profile, "PROFILE_PATH", profile_path)
