from __future__ import annotations

from typing import Optional, Protocol

from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.stored_paths import StoredPaths


class DatalakeStorage(Protocol):
    def save(self, book: BookText) -> StoredPaths: ...

    def paths_of(self, book_id: int) -> Optional[StoredPaths]: ...
