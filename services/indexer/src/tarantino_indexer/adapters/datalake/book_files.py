from __future__ import annotations

from pathlib import Path
from typing import Optional

from tarantino_indexer.model.book.book_text import BookText


class BookFiles:
    @staticmethod
    def book_text(book_id: int, header: Path, body: Path) -> Optional[BookText]:
        if not body.exists():
            return None
        return BookText(
            book_id=book_id,
            header=BookFiles._content(header),
            body=BookFiles._content(body),
            body_path=body,
        )

    @staticmethod
    def _content(file: Path) -> str:
        return file.read_text(encoding="utf-8", newline="")
