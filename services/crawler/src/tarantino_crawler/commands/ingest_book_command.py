from __future__ import annotations

from typing import Optional

from tarantino_crawler.commands.download_result import DownloadResult
from tarantino_crawler.commands.ingest_result import IngestResult
from tarantino_crawler.model.book.gutenberg_text import GutenbergText
from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason
from tarantino_crawler.ports.book_downloader import BookDownloader
from tarantino_crawler.ports.datalake_storage import DatalakeStorage


class IngestBookCommand:

    def __init__(self, downloader: BookDownloader, datalake: DatalakeStorage):
        self._downloader = downloader
        self._datalake = datalake

    def execute(self, book_id: int) -> IngestResult:
        stored = self.stored(book_id)
        return stored if stored is not None else self.store(self.download(book_id))

    def stored(self, book_id: int) -> Optional[IngestResult]:
        paths = self._datalake.paths_of(book_id)
        return IngestResult.success(book_id, paths) if paths is not None else None

    def download(self, book_id: int) -> DownloadResult:
        try:
            raw_text = self._downloader.raw_text(book_id)
            return DownloadResult.success(GutenbergText.book_text(book_id, raw_text))
        except DownloadException as e:
            return DownloadResult.failure_result(book_id, e.reason)

    def store(self, download: DownloadResult) -> IngestResult:
        if not download.succeeded():
            return IngestResult.failure_result(download.book_id, download.failure)
        try:
            return IngestResult.success(
                download.book_id, self._datalake.save(download.text)
            )
        except OSError:
            return IngestResult.failure_result(
                download.book_id, FailureReason.STORAGE_ERROR
            )
