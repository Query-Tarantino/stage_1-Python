from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from tarantino_control.adapters.file_control_state_store import FileControlStateStore
from tarantino_control.adapters.local_crawler import LocalCrawler
from tarantino_control.adapters.local_indexer import LocalIndexer
from tarantino_control.commands.control_pipeline import ControlPipeline
from tarantino_control.control_config import ControlConfig
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
        return ControlPipeline(
            FileControlStateStore(config.control),
            LocalCrawler(CrawlerFactory.ingest_command(crawler)),
            LocalIndexer(IndexerFactory.index_command(indexer)),
            candidates,
        )

    @staticmethod
    def candidates(config: ControlConfig, file: Optional[str]) -> List[int]:
        filename = file if file is not None else ControlFactory.DEFAULT_CANDIDATES
        lines = ControlFactory._lines(config.workload / filename)
        return [int(line.strip()) for line in lines if line.strip()]

    @staticmethod
    def _lines(file_path: Path) -> List[str]:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.readlines()
