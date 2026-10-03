from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set

from tarantino_control.model.whitespace import JAVA_WHITESPACE
from tarantino_control.ports.control_state_store import ControlStateStore


class FileControlStateStore(ControlStateStore):
    BOOK_ID = re.compile(r"[0-9]+")

    def __init__(self, root: Path):
        self._downloaded = root / "downloaded_books.txt"
        self._indexed = root / "indexed_books.txt"

    def downloaded(self) -> Set[int]:
        return self._ids(self._downloaded)

    def indexed(self) -> Set[int]:
        return self._ids(self._indexed)

    def mark_downloaded(self, book_id: int) -> None:
        self._append(self._downloaded, book_id)

    def mark_indexed(self, book_id: int) -> None:
        self._append(self._indexed, book_id)

    @classmethod
    def _ids(cls, file_path: Path) -> Set[int]:
        ids_set = set()
        for line in cls._lines(file_path):
            stripped = line.strip(JAVA_WHITESPACE)
            if cls.BOOK_ID.fullmatch(stripped):
                ids_set.add(int(stripped))
        return ids_set

    @staticmethod
    def _lines(file_path: Path) -> List[str]:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8", newline="\n") as f:
                return f.readlines()
        return []

    @staticmethod
    def _append(file_path: Path, book_id: int) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"{book_id}\n")
