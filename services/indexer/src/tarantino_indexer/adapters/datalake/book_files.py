from __future__ import annotations

from pathlib import Path
from typing import Optional

from tarantino_indexer.model.book.book_text import BookText


class BookFiles:
    @staticmethod
    def book_text(book_id: int, header: Path, body: Path) -> Optional[BookText]:
        # A book exists if and only if its body file does (SPEC §6)
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
        # As written: only \n ends a line, so no line ending is translated (SPEC §1)
        return file.read_text(encoding="utf-8", newline="")
