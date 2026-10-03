from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, Set

from tarantino_crawler.adapters.datalake.book_files import BookFiles
from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.stored_paths import StoredPaths
from tarantino_crawler.ports.datalake_storage import DatalakeStorage


class BatchBasedDatalakeAdapter(DatalakeStorage):
    BATCH_SIZE = 1000
    HEADER_SUFFIX = ".header.txt"
    BODY_SUFFIX = ".body.txt"

    def __init__(self, root: Path):
        self._root = root

    def save(self, book: BookText) -> StoredPaths:
        return BookFiles.write(self._paths(book.book_id), book)

    def paths_of(self, book_id: int) -> Optional[StoredPaths]:
        return BookFiles.existing(self._paths(book_id))

    def ids_stored_since(self, instant: datetime) -> Set[int]:
        since = BookFiles.nanoseconds(instant)
        return {
            BookFiles.book_id(file, self.BODY_SUFFIX)
            for batch in BookFiles.children(self._root)
            for file in BookFiles.children(batch)
            if file.name.endswith(self.BODY_SUFFIX)
            and BookFiles.modified_since(file, since)
        }

    def remove_incomplete_writes(self) -> int:
        return BookFiles.remove_incomplete_writes(self._root)

    def _paths(self, book_id: int) -> StoredPaths:
        directory = self._root / str(book_id // self.BATCH_SIZE)
        return StoredPaths(
            header=directory / f"{book_id}{self.HEADER_SUFFIX}",
            body=directory / f"{book_id}{self.BODY_SUFFIX}",
        )
