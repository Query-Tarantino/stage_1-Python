from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from tarantino_indexer.adapters.datalake.book_files import BookFiles
from tarantino_indexer.model.book.book_text import BookText
from tarantino_indexer.ports.sources.datalake_reader import DatalakeReader


class TimeBasedDatalakeReader(DatalakeReader):
    HEADER_SUFFIX = ".header.txt"
    BODY_SUFFIX = ".body.txt"
    BOOK_FILE_DEPTH = 3

    def __init__(self, root: Path):
        self.root = root

    def book_text(self, book_id: int) -> Optional[BookText]:
        body = self._body_file(book_id)
        if body is None:
            return None
        return BookFiles.book_text(
            book_id, body.with_name(f"{book_id}{self.HEADER_SUFFIX}"), body
        )

    def _body_file(self, book_id: int) -> Optional[Path]:
        if not self.root.is_dir():
            return None
        return self._first_file_named(self.root, f"{book_id}{self.BODY_SUFFIX}", 1)

    def _first_file_named(
        self, directory: Path, name: str, depth: int
    ) -> Optional[Path]:
        # Depth first, down to the book files, stopping at the first match (SPEC §6)
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.name == name:
                    return Path(entry.path)
                if depth < self.BOOK_FILE_DEPTH and entry.is_dir(follow_symlinks=False):
                    found = self._first_file_named(Path(entry.path), name, depth + 1)
                    if found:
                        return found
        return None
