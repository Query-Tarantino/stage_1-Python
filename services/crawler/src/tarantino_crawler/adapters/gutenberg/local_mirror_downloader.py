from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason
from tarantino_crawler.ports.book_downloader import BookDownloader


class LocalMirrorDownloader(BookDownloader):
    BOOK_ID = re.compile(r"[1-9][0-9]{0,8}")

    def __init__(self, mirror: Path):
        self._mirror = mirror

    def raw_text(self, book_id: int) -> str:
        file = self._file(book_id)
        if not file.is_file():
            raise DownloadException(
                FailureReason.NOT_FOUND,
                f"Book {book_id} not found in the mirror {self._mirror}",
            )
        try:
            return file.read_text(encoding="utf-8", newline="")
        except (OSError, UnicodeDecodeError) as error:
            raise DownloadException(
                FailureReason.NETWORK_ERROR,
                f"Could not read book {book_id} from the mirror: {error}",
            ) from error

    def book_ids(self) -> List[int]:
        with os.scandir(self._mirror) as entries:
            ids = [
                int(entry.name)
                for entry in entries
                if self.BOOK_ID.fullmatch(entry.name)
            ]
        return sorted(book_id for book_id in ids if self._file(book_id).is_file())

    def _file(self, book_id: int) -> Path:
        return self._mirror / str(book_id) / f"pg{book_id}.txt"
