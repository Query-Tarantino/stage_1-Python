import sys
from pathlib import Path

import pytest

from tarantino_crawler.__main__ import line, main
from tarantino_crawler.commands.ingest_result import IngestResult
from tarantino_crawler.model.book.stored_paths import StoredPaths
from tarantino_crawler.model.failure.failure_reason import FailureReason


def test_prints_the_directory_where_a_book_is_stored():
    paths = StoredPaths(
        Path("datalake/1342/header.txt"), Path("datalake/1342/body.txt")
    )

    assert (
        line(IngestResult.success(1342, paths))
        == f"[CRAWLER] 1342: stored in {Path('datalake/1342')}"
    )


def test_prints_why_a_book_is_skipped():
    result = IngestResult.failure_result(84, FailureReason.NOT_FOUND)

    assert line(result) == "[CRAWLER] 84: skipped, NOT_FOUND"


def test_stops_before_any_work_when_a_book_id_is_not_an_integer(monkeypatch, tmp_path):
    monkeypatch.setenv("TARANTINO_DATALAKE", str(tmp_path / "datalake"))
    monkeypatch.setattr(sys, "argv", ["tarantino_crawler", "1342", "abc"])

    with pytest.raises(SystemExit) as stop:
        main()

    assert "abc" in str(stop.value.code)
    assert not (tmp_path / "datalake").exists()


def gutenberg_text(title: str, body: str) -> str:
    marker = f" OF THE PROJECT GUTENBERG EBOOK {title.upper()} ***"
    return "\r\n".join(
        [f"Title: {title}", "", f"*** START{marker}", body, f"*** END{marker}", ""]
    )


def test_removes_incomplete_writes_then_ingests_each_book_in_order(
    monkeypatch, tmp_path, capsys
):
    (tmp_path / "mirror" / "11").mkdir(parents=True)
    (tmp_path / "mirror" / "11" / "pg11.txt").write_text(
        gutenberg_text("Alice", "Alice was tired."), encoding="utf-8"
    )
    (tmp_path / "datalake" / "5").mkdir(parents=True)
    (tmp_path / "datalake" / "5" / "header.txt").write_text("header", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARANTINO_DATALAKE", "datalake")
    monkeypatch.setenv("TARANTINO_DATALAKE_LAYOUT", "book")
    monkeypatch.setenv("TARANTINO_MIRROR", "mirror")
    monkeypatch.setattr(sys, "argv", ["tarantino_crawler", "11", "404"])

    main()

    assert capsys.readouterr().out.splitlines() == [
        "Removed 1 files left by an interrupted run from datalake",
        f"[CRAWLER] 11: stored in {Path('datalake/11')}",
        "[CRAWLER] 404: skipped, NOT_FOUND",
    ]
    assert (tmp_path / "datalake" / "11" / "body.txt").read_text(
        encoding="utf-8"
    ) == "Alice was tired."
    assert not (tmp_path / "datalake" / "5").exists()
