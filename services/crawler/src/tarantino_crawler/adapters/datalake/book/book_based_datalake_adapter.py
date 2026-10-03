from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.stored_paths import StoredPaths
from tarantino_crawler.ports.datalake_storage import DatalakeStorage


class BookBasedDatalakeAdapter(DatalakeStorage):
    def __init__(self, root: Path):
        self._root = root

    def save(self, book: BookText) -> StoredPaths:
        dir_path = self._root / str(book.book_id)
        dir_path.mkdir(parents=True, exist_ok=True)

        body_path = dir_path / f"{book.book_id}.body.txt"
        header_path = dir_path / f"{book.book_id}.header.txt"

        tmp_body = body_path.with_suffix(".txt.tmp")
        tmp_body.write_text(book.body, encoding="utf-8")
        os.replace(tmp_body, body_path)

        tmp_header = header_path.with_suffix(".txt.tmp")
        tmp_header.write_text(book.header, encoding="utf-8")
        os.replace(tmp_header, header_path)

        return StoredPaths(header=header_path, body=body_path)

    def paths_of(self, book_id: int) -> Optional[StoredPaths]:
        dir_path = self._root / str(book_id)
        body_path = dir_path / f"{book_id}.body.txt"
        header_path = dir_path / f"{book_id}.header.txt"

        if body_path.exists() and header_path.exists():
            return StoredPaths(header=header_path, body=body_path)
        return None
