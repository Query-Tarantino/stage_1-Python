from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from tarantino_indexer.model.book.book import Book
from tarantino_indexer.ports.datamarts.metadata_storage import MetadataStorage


class SqliteMetadataAdapter(MetadataStorage):
    CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT,
            language TEXT,
            path TEXT NOT NULL
        )
    """
    UPSERT = """
        INSERT OR REPLACE INTO books (book_id, title, author, language, path)
        VALUES (?, ?, ?, ?, ?)
    """

    def __init__(self, database: Path):
        self.database = database
        self._connection: Optional[sqlite3.Connection] = None

    def save(self, book: Book) -> None:
        self._connected().execute(
            self.UPSERT,
            (
                book.book_id,
                book.title,
                book.author,
                book.language,
                book.path.as_posix(),
            ),
        )

    def _connected(self) -> sqlite3.Connection:
        if self._connection is None:
            self.database.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self.database, autocommit=True)
            self._connection.execute(self.CREATE_TABLE)
        return self._connection
