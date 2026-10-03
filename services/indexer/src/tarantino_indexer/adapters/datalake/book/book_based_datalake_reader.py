from __future__ import annotations

from pathlib import Path
from typing import Optional

from tarantino_indexer.adapters.datalake.book_files import BookFiles
from tarantino_indexer.model.book.book_text import BookText
from tarantino_indexer.ports.sources.datalake_reader import DatalakeReader


class BookBasedDatalakeReader(DatalakeReader):
    HEADER_FILE = "header.txt"
    BODY_FILE = "body.txt"

    def __init__(self, root: Path):
        self.root = root

    def book_text(self, book_id: int) -> Optional[BookText]:
        directory = self.root / str(book_id)
        return BookFiles.book_text(
            book_id, directory / self.HEADER_FILE, directory / self.BODY_FILE
        )
