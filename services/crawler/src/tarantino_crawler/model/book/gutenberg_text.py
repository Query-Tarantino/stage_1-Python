from __future__ import annotations

import re

from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason


class GutenbergText:
    _START_MARKER = re.compile(
        r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG EBOOK[^\n]*\n"
    )
    _END_MARKER = re.compile(r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG EBOOK")

    @staticmethod
    def book_text(book_id: int, raw_text: str) -> BookText:
        text = raw_text.replace("\r\n", "\n")

        start_match = GutenbergText._START_MARKER.search(text)
        if not start_match:
            raise DownloadException(
                FailureReason.MISSING_MARKERS,
                f"Missing Gutenberg markers in book {book_id}",
            )

        end_match = GutenbergText._END_MARKER.search(text, start_match.end())
        if not end_match:
            raise DownloadException(
                FailureReason.MISSING_MARKERS,
                f"Missing Gutenberg markers in book {book_id}",
            )

        header = text[: start_match.start()].strip()
        body = text[start_match.end() : end_match.start()].strip()

        return BookText(book_id=book_id, header=header, body=body)
