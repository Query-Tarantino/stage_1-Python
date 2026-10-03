from __future__ import annotations

from concurrent.futures import Executor, Future
from typing import Callable

from tarantino_control.model.outcome import Outcome
from tarantino_control.ports.crawler import Crawler, Download
from tarantino_crawler.commands.ingest_book_command import IngestBookCommand
from tarantino_crawler.commands.ingest_result import IngestResult


class LocalCrawler(Crawler):

    def __init__(self, ingest_command: IngestBookCommand, downloads: Executor):
        self.ingest_command = ingest_command
        self.downloads = downloads

    def ingest(self, book_id: int) -> Future:
        stored = self.ingest_command.stored(book_id)
        if stored is not None:
            already_stored = Future()
            already_stored.set_result(_Ingestion(lambda: stored))
            return already_stored
        return self.downloads.submit(self._downloaded, book_id)

    def _downloaded(self, book_id: int) -> Download:
        download = self.ingest_command.download(book_id)
        return _Ingestion(lambda: self.ingest_command.store(download))


class _Ingestion(Download):
    def __init__(self, ingested: Callable[[], IngestResult]):
        self._ingested = ingested

    def store(self) -> Outcome:
        result = self._ingested()
        if result.succeeded():
            return Outcome.success(f"stored in {result.paths.body.parent}")
        return Outcome.failure(f"skipped, {result.failure.name}")
