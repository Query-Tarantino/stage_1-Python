import sqlite3
from pathlib import Path

import pytest

from tarantino_query.adapters.metadata.sqlite_metadata_reader import (
    SqliteMetadataReader,
)
from tarantino_query.model.book_metadata import BookMetadata


def insert(database: Path, *rows: tuple) -> None:
    with sqlite3.connect(database) as connection:
        connection.executemany("INSERT INTO books VALUES (?, ?, ?, ?, ?)", rows)


@pytest.fixture
def database(tmp_path) -> Path:
    database = tmp_path / "metadata.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE books (book_id INTEGER PRIMARY KEY, title TEXT, author TEXT,"
            " language TEXT, path TEXT NOT NULL)"
        )
    insert(
        database,
        (76, "Huckleberry Finn", "Mark Twain", "English", "datalake/76/body.txt"),
        (74, "Tom Sawyer", "Mark Twain", "English", "datalake/74/body.txt"),
        (84, "Frankenstein", "Mary Shelley", "English", "datalake/84/body.txt"),
    )
    return database


def ids(books: list) -> list:
    return [book.book_id for book in books]


def test_finds_a_book_by_id(database):
    assert SqliteMetadataReader(database).book(84) == BookMetadata(
        84, "Frankenstein", "Mary Shelley", "English", Path("datalake/84/body.txt")
    )
    assert SqliteMetadataReader(database).book(1) is None


def test_finds_books_by_case_insensitive_author_substring_ordered_by_id(database):
    assert ids(SqliteMetadataReader(database).books_by("twain")) == [74, 76]


def test_matches_percent_underscore_and_backslash_literally(database):
    insert(
        database,
        (1, "One", "A_B\\C", "English", "datalake/1/body.txt"),
        (2, "Two", "AxB", "English", "datalake/2/body.txt"),
    )
    reader = SqliteMetadataReader(database)

    assert ids(reader.books_by("a_b\\c")) == [1]
    assert 2 not in ids(reader.books_by("a_b"))
    assert reader.books_by("%") == []


def test_keeps_its_connection_and_sees_books_saved_after_its_first_query(database):
    reader = SqliteMetadataReader(database)
    assert reader.book(1342) is None

    insert(
        database,
        (
            1342,
            "Pride and Prejudice",
            "Jane Austen",
            "English",
            "datalake/1342/body.txt",
        ),
    )

    assert reader.book(1342).title == "Pride and Prejudice"


def test_treats_a_missing_database_as_empty_without_creating_it(tmp_path):
    missing = tmp_path / "missing.db"

    assert SqliteMetadataReader(missing).book(84) is None
    assert SqliteMetadataReader(missing).books_by("twain") == []
    assert not missing.exists()
