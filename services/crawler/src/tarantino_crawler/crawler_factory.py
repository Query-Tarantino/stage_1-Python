from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from tarantino_crawler.adapters.datalake.batch.batch_based_datalake_adapter import (
    BatchBasedDatalakeAdapter,
)
from tarantino_crawler.adapters.datalake.book.book_based_datalake_adapter import (
    BookBasedDatalakeAdapter,
)
from tarantino_crawler.adapters.datalake.time.time_based_datalake_adapter import (
    TimeBasedDatalakeAdapter,
)
from tarantino_crawler.adapters.gutenberg.gutenberg_http_downloader import (
    GutenbergHttpDownloader,
)
from tarantino_crawler.commands.ingest_book_command import IngestBookCommand
from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_crawler.ports.datalake_storage import DatalakeStorage


class CrawlerFactory:
    _DATALAKE_LAYOUTS: Dict[str, Callable[[Path], DatalakeStorage]] = {
        "time": lambda path: TimeBasedDatalakeAdapter(path),
        "book": lambda path: BookBasedDatalakeAdapter(path),
        "batch": lambda path: BatchBasedDatalakeAdapter(path),
    }

    @staticmethod
    def ingest_command(config: CrawlerConfig) -> IngestBookCommand:
        return IngestBookCommand(
            downloader=GutenbergHttpDownloader(),
            datalake=CrawlerFactory.datalake(config),
        )

    @staticmethod
    def datalake(config: CrawlerConfig) -> DatalakeStorage:
        layout_func = CrawlerFactory._DATALAKE_LAYOUTS.get(config.datalake_layout)
        if layout_func is None:
            raise ValueError(f"Unknown datalake layout: {config.datalake_layout}")
        return layout_func(config.datalake)
