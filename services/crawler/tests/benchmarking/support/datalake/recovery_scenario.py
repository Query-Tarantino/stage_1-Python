from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Sequence

from tarantino_crawler.commands.ingest_book_command import IngestBookCommand
from tarantino_crawler.model.book.gutenberg_text import GutenbergText
from tarantino_crawler.ports.book_downloader import BookDownloader
from tarantino_crawler.ports.datalake_storage import DatalakeStorage

from services.crawler.tests.benchmarking.support.datalake.datalake_fixture import (
    DatalakeFixture,
)
from services.crawler.tests.benchmarking.support.datalake.recovery_outcome import (
    RecoveryOutcome,
)
from services.crawler.tests.benchmarking.support.files.directories import Directories


class RecoveryScenario:
    # Half of the books are ingested; the next one is interrupted after its header is
    # written, leaving its body as .tmp; one hour later a new run removes incomplete
    # writes and ingests every book again (SPEC §11, recovery_ok)
    INTERRUPTED_RUN = datetime.fromisoformat("2025-09-25T14:00:00Z")
    RESUMED_RUN = INTERRUPTED_RUN + timedelta(hours=1)

    def __init__(self, layout: str, root: Path, downloader: BookDownloader):
        self._layout = layout
        self._root = root
        self._downloader = downloader

    def run(self, ids: Sequence[int]) -> RecoveryOutcome:
        interrupted_book = len(ids) // 2
        self._ingest(ids[:interrupted_book], self.INTERRUPTED_RUN)
        self._interrupt_while_storing(ids[interrupted_book])
        self._datalake(self.RESUMED_RUN).remove_incomplete_writes()
        self._ingest(ids, self.RESUMED_RUN)
        return RecoveryOutcome(
            self._every_book_stored_once(ids), self._leftover_files(ids)
        )

    def _ingest(self, ids: Sequence[int], run_time: datetime) -> None:
        ingest = IngestBookCommand(self._downloader, self._datalake(run_time))
        for book_id in ids:
            ingest.execute(book_id)

    def _interrupt_while_storing(self, book_id: int) -> None:
        book = GutenbergText.book_text(book_id, self._downloader.raw_text(book_id))
        paths = self._datalake(self.INTERRUPTED_RUN).save(book)
        os.replace(paths.body, paths.body.with_name(paths.body.name + ".tmp"))

    def _every_book_stored_once(self, ids: Sequence[int]) -> bool:
        datalake = self._datalake(self.RESUMED_RUN)
        return self._body_file_count() == len(ids) and all(
            datalake.paths_of(book_id) is not None for book_id in ids
        )

    def _leftover_files(self, ids: Sequence[int]) -> int:
        # Files that are neither the header nor the body of a stored book: .tmp files
        # and orphaned headers
        datalake = self._datalake(self.RESUMED_RUN)
        book_files: List[Path] = []
        for book_id in ids:
            paths = datalake.paths_of(book_id)
            if paths is not None:
                book_files += [paths.header, paths.body]
        stored = set(book_files)
        return Directories.file_count(self._root, lambda file: file not in stored)

    def _body_file_count(self) -> int:
        return Directories.file_count(self._root, self._is_body)

    @staticmethod
    def _is_body(file: Path) -> bool:
        return file.name == "body.txt" or file.name.endswith(".body.txt")

    def _datalake(self, run_time: datetime) -> DatalakeStorage:
        return DatalakeFixture.datalake(self._layout, self._root, lambda: run_time)
