from __future__ import annotations

import sqlite3
from pathlib import Path

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

    def save(self, book: Book) -> None:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database)
        try:
            with conn:
                conn.execute(self.CREATE_TABLE)
                conn.execute(
                    self.UPSERT,
                    (
                        book.book_id,
                        book.title,
                        book.author,
                        book.language,
                        book.path.as_posix(),
                    ),
                )
        finally:
            conn.close()
