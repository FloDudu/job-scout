from job_scout.ingestion import find_offer_files, move_to_errors, move_to_processed


def _make_offer_file(directory, name, content="TITRE: X\n"):
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


def test_find_offer_files_matches_only_ode_txt(tmp_path):
    _make_offer_file(tmp_path, "ODE_2026-01-01_Job_A.txt")
    _make_offer_file(tmp_path, "ODE_2026-01-02_Job_B.txt")
    (tmp_path / "not_an_offer.txt").write_text("irrelevant", encoding="utf-8")

    found = find_offer_files(tmp_path)

    assert [f.name for f in found] == ["ODE_2026-01-01_Job_A.txt", "ODE_2026-01-02_Job_B.txt"]


def test_move_to_processed_moves_file_and_preserves_content(tmp_path):
    original = _make_offer_file(tmp_path, "ODE_2026-01-01_Job_A.txt", content="hello")

    destination = move_to_processed(original, source_dir=tmp_path)

    assert not original.exists()
    assert destination == tmp_path / "ODE_processed" / "ODE_2026-01-01_Job_A.txt"
    assert destination.read_text(encoding="utf-8") == "hello"
    assert find_offer_files(tmp_path) == []


def test_move_to_errors_moves_file_to_error_folder(tmp_path):
    original = _make_offer_file(tmp_path, "ODE_2026-01-01_Job_A.txt")

    destination = move_to_errors(original, source_dir=tmp_path)

    assert not original.exists()
    assert destination == tmp_path / "ODE_errors" / "ODE_2026-01-01_Job_A.txt"


def test_move_to_processed_does_not_overwrite_name_collision(tmp_path):
    first = _make_offer_file(tmp_path, "ODE_2026-01-01_Job_A.txt", content="first")
    move_to_processed(first, source_dir=tmp_path)

    second = _make_offer_file(tmp_path, "ODE_2026-01-01_Job_A.txt", content="second")
    destination = move_to_processed(second, source_dir=tmp_path)

    assert destination.name == "ODE_2026-01-01_Job_A_1.txt"
    assert destination.read_text(encoding="utf-8") == "second"
    assert (tmp_path / "ODE_processed" / "ODE_2026-01-01_Job_A.txt").read_text(
        encoding="utf-8"
    ) == "first"
