import sqlite3
from pathlib import Path
from typing import List, Optional

from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.ports.metadata_reader import MetadataReader


class SqliteMetadataReader(MetadataReader):
    _BOOK_BY_ID = (
        "SELECT book_id, title, author, language, path FROM books WHERE book_id = ?"
    )
    _BOOKS_BY_AUTHOR = "SELECT book_id, title, author, language, path FROM books WHERE author LIKE ? ORDER BY book_id"

    def __init__(self, database: Path):
        self.database = database

    def book(self, book_id: int) -> Optional[BookMetadata]:
        results = self._books(self._BOOK_BY_ID, (book_id,))
        return results[0] if results else None

    def books_by(self, author: str) -> List[BookMetadata]:
        return self._books(self._BOOKS_BY_AUTHOR, (f"%{author}%",))

    def _books(self, query: str, params: tuple) -> List[BookMetadata]:
        if not self.database.exists():
            return []

        with sqlite3.connect(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                BookMetadata(row[0], row[1], row[2], row[3], Path(row[4]))
                for row in rows
            ]
