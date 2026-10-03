from __future__ import annotations

from pathlib import Path
from typing import Optional

from tarantino_indexer.model.book.book_text import BookText
from tarantino_indexer.ports.sources.datalake_reader import DatalakeReader


class TimeBasedDatalakeReader(DatalakeReader):
    HEADER_SUFFIX = ".header.txt"
    BODY_SUFFIX = ".body.txt"

    def __init__(self, root: Path):
        self.root = root

    def book_text(self, book_id: int) -> Optional[BookText]:
        body = self._body_file(book_id)
        if body:
            return self._create_book_text(book_id, body)
        return None

    def _body_file(self, book_id: int) -> Optional[Path]:
        if not self.root.is_dir():
            return None
        return self._first_file_named(f"{book_id}{self.BODY_SUFFIX}")

    def _first_file_named(self, name: str) -> Optional[Path]:
        for file in self.root.rglob(name):
            try:
                rel = file.relative_to(self.root)
                if len(rel.parts) <= 4:
                    return file
            except ValueError:
                pass
        return None

    @classmethod
    def _create_book_text(cls, book_id: int, body: Path) -> BookText:
        header = body.with_name(f"{book_id}{cls.HEADER_SUFFIX}")
        return BookText(
            book_id=book_id,
            header=cls._content(header) if header.exists() else "",
            body=cls._content(body),
            body_path=body,
        )

    @staticmethod
    def _content(file: Path) -> str:
        return file.read_text(encoding="utf-8") if file.exists() else ""
