from __future__ import annotations

from typing import Optional, Protocol

from tarantino_indexer.model.book.book_text import BookText


class DatalakeReader(Protocol):
    def book_text(self, book_id: int) -> Optional[BookText]: ...
