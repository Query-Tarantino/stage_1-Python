from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Set

from tarantino_crawler.adapters.datalake.book_files import BookFiles
from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.stored_paths import StoredPaths
from tarantino_crawler.ports.datalake_storage import DatalakeStorage


class TimeBasedDatalakeAdapter(DatalakeStorage):
    HEADER_SUFFIX = ".header.txt"
    BODY_SUFFIX = ".body.txt"
    BOOK_FILE_DEPTH = 3

    def __init__(self, root: Path, clock: Optional[Callable[[], datetime]] = None):
        self._root = root
        self._clock = clock if clock else lambda: datetime.now(timezone.utc)

    def save(self, book: BookText) -> StoredPaths:
        return BookFiles.write(
            self._paths_in(self._current_directory(), book.book_id), book
        )

    def paths_of(self, book_id: int) -> Optional[StoredPaths]:
        body = self._body_file(book_id)
        return self._paths_in(body.parent, book_id) if body else None

    def ids_stored_since(self, instant: datetime) -> Set[int]:
        first_hour = instant.astimezone(timezone.utc).strftime("%Y%m%d%H")
        return {
            BookFiles.book_id(file, self.BODY_SUFFIX)
            for day in BookFiles.children(self._root)
            for hour in BookFiles.children(day)
            if day.name + hour.name >= first_hour
            for file in BookFiles.children(hour)
            if file.name.endswith(self.BODY_SUFFIX)
        }

    def remove_incomplete_writes(self) -> int:
        return BookFiles.remove_incomplete_writes(self._root)

    def _current_directory(self) -> Path:
        now = self._clock()
        return self._root / now.strftime("%Y%m%d") / now.strftime("%H")

    def _body_file(self, book_id: int) -> Optional[Path]:
        if not self._root.is_dir():
            return None
        return self._first_file_named(self._root, f"{book_id}{self.BODY_SUFFIX}", 1)

    def _first_file_named(
        self, directory: Path, name: str, depth: int
    ) -> Optional[Path]:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.name == name:
                    return Path(entry.path)
                if depth < self.BOOK_FILE_DEPTH and entry.is_dir(follow_symlinks=False):
                    found = self._first_file_named(Path(entry.path), name, depth + 1)
                    if found:
                        return found
        return None

    @classmethod
    def _paths_in(cls, directory: Path, book_id: int) -> StoredPaths:
        return StoredPaths(
            header=directory / f"{book_id}{cls.HEADER_SUFFIX}",
            body=directory / f"{book_id}{cls.BODY_SUFFIX}",
        )
