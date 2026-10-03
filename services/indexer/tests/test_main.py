import sys

import pytest

from tarantino_indexer.__main__ import line, main
from tarantino_indexer.commands.index_result import IndexResult


def test_prints_the_terms_indexed_of_each_book():
    assert (
        line(IndexResult.success(1342, 7012))
        == "[INDEXER] 1342: 7012 unique terms indexed"
    )


def test_prints_the_books_missing_from_the_datalake():
    assert (
        line(IndexResult.not_found(84))
        == "[INDEXER] 84: skipped, not found in the datalake"
    )


def test_stops_before_any_work_when_a_book_id_is_not_an_integer(monkeypatch, tmp_path):
    (tmp_path / "stopwords.txt").write_text("the\n", encoding="utf-8")
    monkeypatch.setenv("TARANTINO_WORKLOAD", str(tmp_path))
    monkeypatch.setenv("TARANTINO_DATAMARTS", str(tmp_path / "datamarts"))
    monkeypatch.setattr(sys, "argv", ["tarantino_indexer", "1342", "abc"])

    with pytest.raises(SystemExit) as stop:
        main()

    assert "abc" in str(stop.value.code)
    assert not (tmp_path / "datamarts").exists()
