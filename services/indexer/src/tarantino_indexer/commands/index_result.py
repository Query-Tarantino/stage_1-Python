from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndexResult:
    book_id: int
    indexed: bool
    unique_terms: int

    @staticmethod
    def success(book_id: int, unique_terms: int) -> IndexResult:
        return IndexResult(book_id, True, unique_terms)

    @staticmethod
    def not_found(book_id: int) -> IndexResult:
        return IndexResult(book_id, False, 0)
