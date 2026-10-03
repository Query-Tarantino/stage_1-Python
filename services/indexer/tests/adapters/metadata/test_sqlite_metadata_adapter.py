import sqlite3
from pathlib import Path

from tarantino_indexer.adapters.metadata import sqlite_metadata_adapter
from tarantino_indexer.adapters.metadata.sqlite_metadata_adapter import (
    SqliteMetadataAdapter,
)
from tarantino_indexer.model.book.book import Book


def rows(database: Path) -> list:
    with sqlite3.connect(database) as connection:
        return connection.execute("SELECT * FROM books ORDER BY book_id").fetchall()


def test_creates_the_database_and_replaces_saved_books(tmp_path):
    database = tmp_path / "datamarts" / "metadata.db"
    metadata = SqliteMetadataAdapter(database)
    metadata.save(
        Book(5, "Old title", None, "English", Path("datalake", "5", "body.txt"))
    )
    metadata.save(
        Book(
            5,
            "Robinson Crusoe",
            "Daniel Defoe",
            "English",
            Path("datalake", "5", "body.txt"),
        )
    )

    assert rows(database) == [
        (5, "Robinson Crusoe", "Daniel Defoe", "English", "datalake/5/body.txt")
    ]


def test_stores_missing_fields_as_null(tmp_path):
    database = tmp_path / "metadata.db"
    SqliteMetadataAdapter(database).save(Book(7, None, None, None, Path("7.body.txt")))

    assert rows(database) == [(7, None, None, None, "7.body.txt")]


def test_commits_every_save_before_it_returns(tmp_path):
    database = tmp_path / "metadata.db"
    metadata = SqliteMetadataAdapter(database)
    metadata.save(Book(5, "Robinson Crusoe", None, None, Path("5.body.txt")))

    assert rows(database) == [(5, "Robinson Crusoe", None, None, "5.body.txt")]


def test_opens_one_connection_at_the_first_save(tmp_path, monkeypatch):
    database = tmp_path / "metadata.db"
    connections = []
    connect = sqlite3.connect

    def recording_connect(*args, **kwargs):
        connections.append(kwargs)
        return connect(*args, **kwargs)

    monkeypatch.setattr(sqlite_metadata_adapter.sqlite3, "connect", recording_connect)
    metadata = SqliteMetadataAdapter(database)
    assert not database.exists()

    metadata.save(Book(5, "Robinson Crusoe", None, None, Path("5.body.txt")))
    metadata.save(Book(84, "Frankenstein", None, None, Path("84.body.txt")))

    assert connections == [{"autocommit": True}]
