from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.stored_paths import StoredPaths


class BookFiles:
    TEMPORARY_SUFFIX = ".tmp"
    # Every layout names its files <prefix>header.txt and <prefix>body.txt (SPEC §6)
    HEADER_NAME = "header.txt"
    BODY_NAME = "body.txt"
    EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

    @staticmethod
    def write(paths: StoredPaths, book: BookText) -> StoredPaths:
        # The header first: a book exists if and only if its body file does (SPEC §6)
        BookFiles._write_atomically(paths.header, book.header)
        BookFiles._write_atomically(paths.body, book.body)
        return paths

    @staticmethod
    def existing(paths: StoredPaths) -> Optional[StoredPaths]:
        return paths if paths.body.exists() else None

    @staticmethod
    def children(directory: Path) -> List[Path]:
        if not directory.is_dir():
            return []
        with os.scandir(directory) as entries:
            return [Path(entry.path) for entry in entries]

    @staticmethod
    def nanoseconds(instant: datetime) -> int:
        return (instant - BookFiles.EPOCH) // timedelta(microseconds=1) * 1000

    @staticmethod
    def modified_since(file: Path, nanoseconds: int) -> bool:
        # At the full precision the file system keeps: nanoseconds on APFS and ext4
        # (SPEC §6)
        try:
            return file.stat().st_mtime_ns >= nanoseconds
        except FileNotFoundError:
            return False

    @staticmethod
    def book_id(file: Path, suffix: str) -> int:
        return int(file.name[: -len(suffix)])

    @staticmethod
    def remove_incomplete_writes(root: Path) -> int:
        # Every .tmp file, every header whose body does not exist next to it, and every
        # directory under the root left empty (SPEC §6)
        if not root.is_dir():
            return 0
        incomplete = [
            Path(directory, name)
            for directory, _, names in os.walk(root)
            for name in names
            if BookFiles._is_incomplete(Path(directory, name))
        ]
        for file in incomplete:
            file.unlink()
        for directory, _, _ in os.walk(root, topdown=False):
            if Path(directory) != root and not os.listdir(directory):
                os.rmdir(directory)
        return len(incomplete)

    @staticmethod
    def _is_incomplete(file: Path) -> bool:
        name = file.name
        if name.endswith(BookFiles.TEMPORARY_SUFFIX):
            return True
        body = name.replace(BookFiles.HEADER_NAME, BookFiles.BODY_NAME)
        return (
            name.endswith(BookFiles.HEADER_NAME) and not file.with_name(body).exists()
        )

    @staticmethod
    def _write_atomically(target: Path, content: str) -> None:
        temporary = target.with_name(target.name + BookFiles.TEMPORARY_SUFFIX)
        target.parent.mkdir(parents=True, exist_ok=True)
        # UTF-8 with \n line endings on every operating system (SPEC §1)
        temporary.write_text(content, encoding="utf-8", newline="\n")
        os.replace(temporary, target)
