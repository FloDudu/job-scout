import pytest

from job_scout.enrichment import OfferEnrichment, WorkMode, enrich_offer


class FakeParsedResponse:
    def __init__(self, parsed_output, stop_reason="end_turn"):
        self.parsed_output = parsed_output
        self.stop_reason = stop_reason


def test_enrich_offer_returns_the_parsed_output(monkeypatch):
    expected = OfferEnrichment(location="Montreal, QC", work_mode=WorkMode.REMOTE, salary="100k")
    monkeypatch.setattr(
        "job_scout.enrichment.anthropic_client.messages.parse",
        lambda **kwargs: FakeParsedResponse(expected),
    )

    result = enrich_offer("Fully remote role based in Montreal, QC, paying 100k.")

    assert result is expected


def test_enrich_offer_includes_the_description_in_the_prompt(monkeypatch):
    captured = {}

    def fake_parse(**kwargs):
        captured.update(kwargs)
        empty = OfferEnrichment(location="", work_mode=WorkMode.UNKNOWN, salary="")
        return FakeParsedResponse(empty)

    monkeypatch.setattr("job_scout.enrichment.anthropic_client.messages.parse", fake_parse)

    enrich_offer("A very specific description marker XYZ123.")

    prompt = captured["messages"][0]["content"]
    assert "A very specific description marker XYZ123." in prompt


def test_enrich_offer_raises_when_parsed_output_is_none(monkeypatch):
    monkeypatch.setattr(
        "job_scout.enrichment.anthropic_client.messages.parse",
        lambda **kwargs: FakeParsedResponse(None, stop_reason="max_tokens"),
    )

    with pytest.raises(RuntimeError, match="max_tokens"):
        enrich_offer("Some description.")
