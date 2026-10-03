import sqlite3
from pathlib import Path
from typing import List, Optional

from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.ports.metadata_reader import MetadataReader


class SqliteMetadataReader(MetadataReader):
    _BOOK_BY_ID = (
        "SELECT book_id, title, author, language, path FROM books WHERE book_id = ?"
    )
    _BOOKS_BY_AUTHOR = (
        "SELECT book_id, title, author, language, path FROM books"
        " WHERE author LIKE ? ESCAPE '\\' ORDER BY book_id"
    )

    def __init__(self, database: Path):
        self.database = database
        self._connection: Optional[sqlite3.Connection] = None

    def book(self, book_id: int) -> Optional[BookMetadata]:
        results = self._books(self._BOOK_BY_ID, (book_id,))
        return results[0] if results else None

    def books_by(self, author: str) -> List[BookMetadata]:
        return self._books(self._BOOKS_BY_AUTHOR, (f"%{self._literal(author)}%",))

    @staticmethod
    def _literal(author: str) -> str:
        # The author as a LIKE pattern that matches it literally: its \, % and _ are
        # escaped with \ (SPEC §8.2)
        return author.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def _books(self, query: str, params: tuple) -> List[BookMetadata]:
        # Without metadata.db there are no books, and it is not created (SPEC §8.2)
        if self._connection is None and not self.database.exists():
            return []
        rows = self._connected().execute(query, params).fetchall()
        return [
            BookMetadata(row[0], row[1], row[2], row[3], Path(row[4])) for row in rows
        ]

    def _connected(self) -> sqlite3.Connection:
        # One connection, opened at the first query and then reused (SPEC §8.2)
        if self._connection is None:
            self._connection = sqlite3.connect(self.database, autocommit=True)
        return self._connection
