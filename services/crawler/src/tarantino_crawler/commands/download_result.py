from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.failure.failure_reason import FailureReason


@dataclass(frozen=True)
class DownloadResult:
    book_id: int
    text: Optional[BookText]
    failure: Optional[FailureReason]

    @staticmethod
    def success(text: BookText) -> DownloadResult:
        return DownloadResult(book_id=text.book_id, text=text, failure=None)

    @staticmethod
    def failure_result(book_id: int, reason: FailureReason) -> DownloadResult:
        return DownloadResult(book_id=book_id, text=None, failure=reason)

    def succeeded(self) -> bool:
        return self.failure is None
