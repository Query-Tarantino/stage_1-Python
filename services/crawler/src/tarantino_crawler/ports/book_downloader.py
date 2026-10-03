from __future__ import annotations

from typing import Protocol


class BookDownloader(Protocol):
    def raw_text(self, book_id: int) -> str: ...
