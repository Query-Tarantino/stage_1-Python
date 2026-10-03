from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from tarantino_crawler.model.book.book_text import BookText
from tarantino_crawler.model.book.stored_paths import StoredPaths


class BookFiles:
    TEMPORARY_SUFFIX = ".tmp"

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
    def _write_atomically(target: Path, content: str) -> None:
        temporary = target.with_name(target.name + BookFiles.TEMPORARY_SUFFIX)
        target.parent.mkdir(parents=True, exist_ok=True)
        # UTF-8 with \n line endings on every operating system (SPEC §1)
        temporary.write_text(content, encoding="utf-8", newline="\n")
        os.replace(temporary, target)
