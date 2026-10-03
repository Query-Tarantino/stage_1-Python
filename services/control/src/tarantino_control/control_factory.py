from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional

from tarantino_control.adapters.file_control_state_store import FileControlStateStore
from tarantino_control.adapters.local_crawler import LocalCrawler
from tarantino_control.adapters.local_indexer import LocalIndexer
from tarantino_control.commands.control_pipeline import ControlPipeline
from tarantino_control.control_config import ControlConfig
from tarantino_control.model.whitespace import JAVA_WHITESPACE
from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_crawler.crawler_factory import CrawlerFactory
from tarantino_indexer.indexer_config import IndexerConfig
from tarantino_indexer.indexer_factory import IndexerFactory


class ControlFactory:
    DEFAULT_CANDIDATES = "sample_ids.txt"

    @staticmethod
    def pipeline(
        config: ControlConfig,
        crawler: CrawlerConfig,
        indexer: IndexerConfig,
        candidates: List[int],
    ) -> ControlPipeline:
        ingest = CrawlerFactory.ingest_command(crawler)
        index = IndexerFactory.index_command(indexer)
        # Once what an interrupted run left in the datalake is removed (SPEC §6)
        CrawlerFactory.remove_incomplete_writes(crawler)
        # A thread per download, at most parallel_downloads: waiting on the network
        # releases the GIL (SPEC §9)
        downloads = ThreadPoolExecutor(
            max_workers=config.parallel_downloads, thread_name_prefix="download"
        )
        return ControlPipeline(
            FileControlStateStore(config.control),
            LocalCrawler(ingest, downloads),
            LocalIndexer(index),
            candidates,
            config.parallel_downloads,
            config.index_batch,
        )

    @staticmethod
    def candidates(
        config: ControlConfig, crawler: CrawlerConfig, file: Optional[str]
    ) -> List[int]:
        # The ids of the workload file given, in order; without one, every book of the
        # local mirror in ascending id order when there is a mirror, or else the sample
        # dataset (SPEC §9)
        if file is None and crawler.mirror is not None:
            return CrawlerFactory.mirror_book_ids(crawler)
        filename = file if file is not None else ControlFactory.DEFAULT_CANDIDATES
        lines = ControlFactory._lines(config.workload / filename)
        entries = (line.strip(JAVA_WHITESPACE) for line in lines)
        return [int(entry) for entry in entries if entry]

    @staticmethod
    def _lines(file_path: Path) -> List[str]:
        # Only \n ends a line (SPEC §1)
        return file_path.read_text(encoding="utf-8", newline="").split("\n")
