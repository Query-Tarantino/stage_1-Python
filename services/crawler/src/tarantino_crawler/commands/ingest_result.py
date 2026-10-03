from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tarantino_crawler.model.book.stored_paths import StoredPaths
from tarantino_crawler.model.failure.failure_reason import FailureReason


@dataclass(frozen=True)
class IngestResult:
    book_id: int
    paths: Optional[StoredPaths]
    failure: Optional[FailureReason]

    @staticmethod
    def success(book_id: int, paths: StoredPaths) -> IngestResult:
        return IngestResult(book_id=book_id, paths=paths, failure=None)

    @staticmethod
    def failure_result(book_id: int, reason: FailureReason) -> IngestResult:
        return IngestResult(book_id=book_id, paths=None, failure=reason)

    def succeeded(self) -> bool:
        return self.failure is None
