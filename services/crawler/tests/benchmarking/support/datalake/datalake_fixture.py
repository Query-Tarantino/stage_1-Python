from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from tarantino_crawler.adapters.datalake.time.time_based_datalake_adapter import (
    TimeBasedDatalakeAdapter,
)
from tarantino_crawler.commands.ingest_book_command import IngestBookCommand
from tarantino_crawler.commands.ingest_result import IngestResult
from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_crawler.crawler_factory import CrawlerFactory
from tarantino_crawler.model.book.stored_paths import StoredPaths
from tarantino_crawler.ports.book_downloader import BookDownloader
from tarantino_crawler.ports.datalake_storage import DatalakeStorage

from services.crawler.tests.benchmarking.support.datalake.crawl_clock import CrawlClock
from services.crawler.tests.benchmarking.support.files.directories import Directories
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow
from services.crawler.tests.benchmarking.support.validation.check import Check

Clock = Callable[[], datetime]


class DatalakeFixture:
    LAYOUTS = ("time", "book", "batch")
    CRAWL_START = datetime(2025, 9, 25, tzinfo=timezone.utc)

    @staticmethod
    def datalake(
        layout: str, root: Path, clock: Optional[Clock] = None
    ) -> DatalakeStorage:
        if layout == "time":
            return TimeBasedDatalakeAdapter(root, clock)
        return CrawlerFactory.datalake(CrawlerConfig(root, layout))

    @staticmethod
    def ingest(
        datalake: DatalakeStorage, ids: Sequence[int], downloader: BookDownloader
    ) -> List[StoredPaths]:
        ingest = IngestBookCommand(downloader, datalake)
        return [DatalakeFixture._stored(ingest.execute(book_id)) for book_id in ids]

    @staticmethod
    def ingest_as_crawled(
        layout: str,
        root: Path,
        ids: Sequence[int],
        downloader: BookDownloader,
        start: datetime,
    ) -> List[StoredPaths]:
        clock = CrawlClock(start)
        ingest = IngestBookCommand(
            downloader, DatalakeFixture.datalake(layout, root, clock)
        )
        stored = []
        for position, book_id in enumerate(ids):
            clock.move_to(position)
            stored.append(DatalakeFixture._stored(ingest.execute(book_id)))
        return stored

    @staticmethod
    def footprint(layout: str, books: int, root: Path) -> List[ResultRow]:
        footprint = Directories.footprint(root)
        return [
            ResultRow.exact(layout, "file_count", books, footprint.files, "files"),
            ResultRow.exact(
                layout, "directory_count", books, footprint.directories, "dirs"
            ),
            ResultRow.exact(layout, "disk_usage", books, footprint.bytes, "bytes"),
            ResultRow.exact(
                layout, "disk_allocated", books, footprint.allocated_bytes, "bytes"
            ),
        ]

    @staticmethod
    def _stored(result: IngestResult) -> StoredPaths:
        Check.require(
            result.succeeded(),
            f"book {result.book_id} not ingested: {result.failure}",
        )
        return result.paths
