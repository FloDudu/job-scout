from job_scout.parser import parse_offer

WELL_FORMED = """TITRE: Software Engineer
ENTREPRISE: Acme Corp
LOCALISATION: Montreal, QC

DESCRIPTION:
Line one of the description.
Line two, with more details.
"""


def test_parses_all_fields():
    offer = parse_offer(WELL_FORMED)

    assert offer.title == "Software Engineer"
    assert offer.company == "Acme Corp"
    assert offer.location == "Montreal, QC"
    assert offer.description == "Line one of the description.\nLine two, with more details."


def test_empty_location_field():
    raw = "TITRE: X\nENTREPRISE: Y\nLOCALISATION: \n\nDESCRIPTION:\nBody text\n"

    offer = parse_offer(raw)

    assert offer.location == ""
    assert offer.title == "X"


def test_missing_location_line():
    raw = "TITRE: X\nENTREPRISE: Y\n\nDESCRIPTION:\nBody text\n"

    offer = parse_offer(raw)

    assert offer.location == ""
    assert offer.title == "X"
    assert offer.company == "Y"


def test_missing_description_marker_does_not_crash():
    raw = "TITRE: X\nENTREPRISE: Y\nLOCALISATION: Z\n"

    offer = parse_offer(raw)

    assert offer.title == "X"
    assert offer.description == ""


def test_empty_input_does_not_crash():
    offer = parse_offer("")

    assert offer == parse_offer("")
    assert offer.title == ""
    assert offer.company == ""
    assert offer.location == ""
    assert offer.description == ""


def test_garbage_input_does_not_crash():
    offer = parse_offer("this text has no recognizable structure at all")

    assert offer.title == ""
    assert offer.description == ""


def test_field_like_text_inside_description_is_not_mistaken_for_a_header():
    raw = (
        "TITRE: Real Title\n"
        "ENTREPRISE: Real Company\n"
        "LOCALISATION: Real Location\n\n"
        "DESCRIPTION:\n"
        "Ideal candidate profile:\n"
        "TITRE: Bachelor's degree required\n"
        "ENTREPRISE: 2+ years of experience\n"
    )

    offer = parse_offer(raw)

    assert offer.title == "Real Title"
    assert offer.company == "Real Company"
    assert "TITRE: Bachelor's degree required" in offer.description
