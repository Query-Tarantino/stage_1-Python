from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.stored_paths import StoredPaths
from tarantino_crawler.ports.datalake_storage import DatalakeStorage


class TimeBasedDatalakeAdapter(DatalakeStorage):
    def __init__(self, root: Path, clock: Optional[Callable[[], datetime]] = None):
        self._root = root
        self._clock = clock if clock else lambda: datetime.now(timezone.utc)

    def save(self, book: BookText) -> StoredPaths:
        now = self._clock()
        dir_path = self._root / now.strftime("%Y%m%d") / now.strftime("%H")
        dir_path.mkdir(parents=True, exist_ok=True)

        header_path = dir_path / f"{book.book_id}.header.txt"
        body_path = dir_path / f"{book.book_id}.body.txt"

        self._atomic_write(header_path, book.header)
        self._atomic_write(body_path, book.body)

        return StoredPaths(header=header_path, body=body_path)

    def _atomic_write(self, target: Path, content: str) -> None:
        tmp_path = target.with_suffix(target.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, target)

    def paths_of(self, book_id: int) -> Optional[StoredPaths]:
        for body_path in self._root.rglob(f"{book_id}.body.txt"):
            header_path = body_path.with_name(f"{book_id}.header.txt")
            if header_path.exists():
                return StoredPaths(header=header_path, body=body_path)
        return None
