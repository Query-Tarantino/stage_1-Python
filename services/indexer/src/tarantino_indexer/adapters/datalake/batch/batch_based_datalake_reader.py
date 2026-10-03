from __future__ import annotations

from pathlib import Path
from typing import Optional

from tarantino_indexer.model.book.book_text import BookText
from tarantino_indexer.ports.sources.datalake_reader import DatalakeReader


class BatchBasedDatalakeReader(DatalakeReader):
    def __init__(self, root: Path):
        self.root = root

    def book_text(self, book_id: int) -> Optional[BookText]:
        batch_id = str(book_id // 1000)
        dir_path = self.root / batch_id
        body_path = dir_path / f"{book_id}.body.txt"
        header_path = dir_path / f"{book_id}.header.txt"

        if body_path.exists() and header_path.exists():
            body = body_path.read_text(encoding="utf-8")
            header = header_path.read_text(encoding="utf-8")
            return BookText(
                book_id=book_id, header=header, body=body, body_path=body_path
            )
        return None
