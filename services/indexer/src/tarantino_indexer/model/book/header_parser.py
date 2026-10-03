from __future__ import annotations

import re
from typing import Optional

from tarantino_indexer.model.book.book import Book
from tarantino_indexer.model.book.book_text import BookText
from tarantino_indexer.model.whitespace import JAVA_WHITESPACE


class HeaderParser:
    TITLE = re.compile(r"^Title:[ \t]*(.+)$", re.MULTILINE)
    AUTHOR = re.compile(r"^Author:[ \t]*(.+)$", re.MULTILINE)
    LANGUAGE = re.compile(r"^Language:[ \t]*(.+)$", re.MULTILINE)

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
        return match.group(1).strip(JAVA_WHITESPACE) if match else None
