from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import List, Set

from tarantino_crawler.model.book.stored_paths import StoredPaths

from services.crawler.tests.benchmarking.support.datalake.crawl_clock import CrawlClock
from services.crawler.tests.benchmarking.support.datalake.datalake_fixture import (
    DatalakeFixture,
)
from services.crawler.tests.benchmarking.support.dataset.benchmark_dataset import (
    BenchmarkDataset,
)
from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)
from services.crawler.tests.benchmarking.support.files.directories import Directories
from services.crawler.tests.benchmarking.support.harness.benchmark import (
    Benchmark,
    timed_operation,
)
from services.crawler.tests.benchmarking.support.validation.check import Check


class NewBooksDetectionBenchmark(Benchmark):
    STRUCTURES = DatalakeFixture.LAYOUTS
    AGE_OF_OLD_BOOKS = timedelta(days=1)
    EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

    def setup_trial(self) -> None:
        # The N books of the dataset end one day before the new ones, which are then
        # saved at the current time (SPEC §11)
        dataset = BenchmarkDataset.from_environment()
        self._root = BenchmarkPaths.scratch(
            f"datalake-detection-{self.structure}-{self.books}"
        )
        Directories.delete(self._root)
        self._last_run = datetime.now(timezone.utc)
        self._store_old_books(dataset.ids(self.books), dataset)
        self._datalake = DatalakeFixture.datalake(self.structure, self._root)
        new_ids = dataset.new_ids()
        DatalakeFixture.ingest(self._datalake, new_ids, dataset)
        Check.require(
            self._datalake.ids_stored_since(self._last_run) == set(new_ids),
            "detection did not list exactly the new books",
        )

    @timed_operation()
    def new_books_detection_time(self) -> Set[int]:
        return self._datalake.ids_stored_since(self._last_run)

    def teardown_trial(self) -> None:
        Directories.delete(self._root)

    def _store_old_books(self, ids: List[int], dataset: BenchmarkDataset) -> None:
        # Their simulated download time is also the modification time of each body,
        # which book and batch read (SPEC §11)
        crawl_start = (
            self._last_run - self.AGE_OF_OLD_BOOKS - CrawlClock.duration_of(len(ids))
        )
        stored = DatalakeFixture.ingest_as_crawled(
            self.structure, self._root, ids, dataset, crawl_start
        )
        for position, paths in enumerate(stored):
            self._age(paths, CrawlClock.instant_of(crawl_start, position))

    def _age(self, paths: StoredPaths, instant: datetime) -> None:
        nanoseconds = (instant - self.EPOCH) // timedelta(microseconds=1) * 1000
        accessed = paths.body.stat().st_atime_ns
        os.utime(paths.body, ns=(accessed, nanoseconds))
