from __future__ import annotations

import re
from typing import Optional

from tarantino_indexer.model.book.book import Book
from tarantino_indexer.model.book.book_text import BookText


class HeaderParser:
    TITLE = re.compile(r"^Title:[ \t]*(.+)$", re.MULTILINE | re.IGNORECASE)
    AUTHOR = re.compile(r"^Author:[ \t]*(.+)$", re.MULTILINE | re.IGNORECASE)
    LANGUAGE = re.compile(r"^Language:[ \t]*(.+)$", re.MULTILINE | re.IGNORECASE)

    def book(self, text: BookText) -> Book:
        return Book(
            book_id=text.book_id,
            title=self._field(self.TITLE, text),
            author=self._field(self.AUTHOR, text),
            language=self._field(self.LANGUAGE, text),
            path=text.body_path,
        )

    @staticmethod
    def _field(pattern: re.Pattern, text: BookText) -> Optional[str]:
        match = pattern.search(text.header)
        return match.group(1).strip() if match else None
