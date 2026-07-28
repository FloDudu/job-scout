from job_scout.enrichment import OfferEnrichment, WorkMode, enrich_offer


class FakeParsedResponse:
    def __init__(self, parsed_output):
        self.parsed_output = parsed_output


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
