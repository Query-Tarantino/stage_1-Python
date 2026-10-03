import sqlite3
import sys
from pathlib import Path

import pytest

from tarantino_query.__main__ import line, main
from tarantino_query.model.book_metadata import BookMetadata


def test_prints_each_book_with_its_metadata():
    path = Path("datalake/1342/body.txt")
    book = BookMetadata(1342, "Pride and Prejudice", "Jane Austen", "English", path)

    assert line(book) == f"  [1342] Pride and Prejudice — Jane Austen (English) {path}"


def test_writes_missing_fields_as_null():
    path = Path("datalake/2/body.txt")
    book = BookMetadata(2, "No Author Here", None, None, path)

    assert line(book) == f"  [2] No Author Here — null (null) {path}"


def search_from_the_command_line(monkeypatch, root: Path, *words: str) -> None:
    (root / "workload").mkdir()
    (root / "workload" / "stopwords.txt").write_text("the\n", encoding="utf-8")
    (root / "datamarts").mkdir()
    (root / "datamarts" / "inverted_index.json").write_text(
        '{"sister":[84,11],"tired":[11]}', encoding="utf-8"
    )
    with sqlite3.connect(root / "datamarts" / "metadata.db") as connection:
        connection.execute(
            "CREATE TABLE books (book_id INTEGER PRIMARY KEY, title TEXT, author TEXT,"
            " language TEXT, path TEXT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            [
                (11, "Alice", "Lewis Carroll", "English", "datalake/11/body.txt"),
                (84, "Frankenstein", None, None, "datalake/84/body.txt"),
            ],
        )
    connection.close()
    monkeypatch.chdir(root)
    monkeypatch.setenv("TARANTINO_DATAMARTS", "datamarts")
    monkeypatch.setenv("TARANTINO_INDEX", "json")
    monkeypatch.setenv("TARANTINO_METADATA", "sqlite")
    monkeypatch.setenv("TARANTINO_WORKLOAD", "workload")
    monkeypatch.setattr(sys, "argv", ["tarantino_query", *words])
    main()


def test_joins_the_words_of_the_command_line_and_prints_every_book_found(
    monkeypatch, tmp_path, capsys
):
    search_from_the_command_line(monkeypatch, tmp_path, "the", "Sister")

    assert capsys.readouterr().out.splitlines() == [
        '2 result(s) for "the Sister"',
        f"  [11] Alice — Lewis Carroll (English) {Path('datalake/11/body.txt')}",
        f"  [84] Frankenstein — null (null) {Path('datalake/84/body.txt')}",
    ]


def test_prints_no_books_when_none_has_every_word(monkeypatch, tmp_path, capsys):
    search_from_the_command_line(monkeypatch, tmp_path, "tired", "whale")

    assert capsys.readouterr().out.splitlines() == ['0 result(s) for "tired whale"']


def test_stops_before_any_work_with_an_unknown_index(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARANTINO_INDEX", "trie")
    monkeypatch.setattr(sys, "argv", ["tarantino_query", "whale"])

    with pytest.raises(SystemExit) as stop:
        main()

    assert stop.value.code == "tarantino_query: Unknown index structure: trie"
