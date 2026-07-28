from job_scout.letter import generate_cover_letter


class FakeBlock:
    def __init__(self, type_, text=""):
        self.type = type_
        self.text = text


class FakeMessage:
    def __init__(self, content):
        self.content = content


def test_generate_cover_letter_extracts_the_text_block(monkeypatch):
    monkeypatch.setattr(
        "job_scout.letter.anthropic_client.messages.create",
        lambda **kwargs: FakeMessage([FakeBlock("text", "Dear hiring manager, ...")]),
    )

    result = generate_cover_letter("Backend Engineer", "Acme Corp", "Build things.", "report", "en")

    assert result == "Dear hiring manager, ..."


def test_generate_cover_letter_skips_a_leading_non_text_block(monkeypatch):
    monkeypatch.setattr(
        "job_scout.letter.anthropic_client.messages.create",
        lambda **kwargs: FakeMessage(
            [FakeBlock("thinking", "internal reasoning"), FakeBlock("text", "Cher recruteur, ...")]
        ),
    )

    result = generate_cover_letter("Backend Engineer", "Acme Corp", "Build things.", "report", "fr")

    assert result == "Cher recruteur, ..."


def test_generate_cover_letter_passes_the_right_language_name(monkeypatch):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return FakeMessage([FakeBlock("text", "...")])

    monkeypatch.setattr("job_scout.letter.anthropic_client.messages.create", fake_create)

    generate_cover_letter("Backend Engineer", "Acme Corp", "Build things.", "report", "fr")

    prompt = captured["messages"][0]["content"]
    assert "French" in prompt
