from __future__ import annotations

from typing import Protocol

from tarantino_indexer.model.book.book import Book


class MetadataStorage(Protocol):
    def save(self, book: Book) -> None: ...
