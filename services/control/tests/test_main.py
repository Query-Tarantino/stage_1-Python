from pathlib import Path

import pytest

from tarantino_control.__main__ import main


def test_stops_before_any_work_without_the_candidates_file(monkeypatch, tmp_path):
    monkeypatch.setenv("TARANTINO_WORKLOAD", str(tmp_path))
    monkeypatch.setenv("TARANTINO_CONTROL", str(tmp_path / "control"))
    monkeypatch.setenv("TARANTINO_DATALAKE", str(tmp_path / "datalake"))

    with pytest.raises(SystemExit) as stop:
        main(["missing.txt"])

    assert "missing.txt" in str(stop.value.code)
    assert not (tmp_path / "control").exists()
    assert not (tmp_path / "datalake").exists()


def test_stops_before_any_work_with_an_invalid_number_of_downloads(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARANTINO_PARALLEL_DOWNLOADS", "0")

    with pytest.raises(SystemExit) as stop:
        main([])

    assert stop.value.code == (
        "tarantino_control: Unknown TARANTINO_PARALLEL_DOWNLOADS: 0"
        " (expected a positive integer)"
    )
    assert list(tmp_path.iterdir()) == []


def gutenberg_text(title: str, body: str) -> str:
    marker = f" OF THE PROJECT GUTENBERG EBOOK {title.upper()} ***"
    return "\r\n".join(
        [f"Title: {title}", "", f"*** START{marker}", body, f"*** END{marker}", ""]
    )


def test_prints_one_line_per_step_until_nothing_is_left_to_do(
    monkeypatch, tmp_path, capsys
):
    # One download at a time, so the steps come in a fixed order
    books = {11: "whale island whale", 84: "island sea", 2000: "rocín flaco galgo"}
    for book_id, body in books.items():
        (tmp_path / "mirror" / str(book_id)).mkdir(parents=True)
        (tmp_path / "mirror" / str(book_id) / f"pg{book_id}.txt").write_text(
            gutenberg_text(f"Book {book_id}", body), encoding="utf-8"
        )
    (tmp_path / "workload").mkdir()
    (tmp_path / "workload" / "stopwords.txt").write_text("the\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    environment = {
        "TARANTINO_CONTROL": "control",
        "TARANTINO_DATALAKE": "datalake",
        "TARANTINO_DATALAKE_LAYOUT": "book",
        "TARANTINO_DATAMARTS": "datamarts",
        "TARANTINO_INDEX": "json",
        "TARANTINO_METADATA": "sqlite",
        "TARANTINO_MIRROR": "mirror",
        "TARANTINO_WORKLOAD": "workload",
        "TARANTINO_PARALLEL_DOWNLOADS": "1",
        "TARANTINO_INDEX_BATCH": "2",
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    main([])

    assert capsys.readouterr().out.splitlines() == [
        f"[CONTROL] DOWNLOAD 11: stored in {Path('datalake/11')}",
        f"[CONTROL] DOWNLOAD 84: stored in {Path('datalake/84')}",
        "[CONTROL] INDEX 2 books (11…84): 2 indexed",
        f"[CONTROL] DOWNLOAD 2000: stored in {Path('datalake/2000')}",
        "[CONTROL] INDEX 2000: 3 unique terms indexed",
        "[CONTROL] Nothing left to do",
    ]
    assert (tmp_path / "control" / "indexed_books.txt").read_text().split() == [
        "11",
        "84",
        "2000",
    ]
