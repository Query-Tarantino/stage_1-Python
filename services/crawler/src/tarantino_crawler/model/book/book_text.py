from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookText:
    book_id: int
    header: str
    body: str
