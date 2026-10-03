from __future__ import annotations

import random
from typing import Optional

from tarantino_crawler.model.book.stored_paths import StoredPaths

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
from services.crawler.tests.benchmarking.support.harness.iterations import (
    MICROSECONDS,
)
from services.crawler.tests.benchmarking.support.validation.check import Check


class DatalakeLookupBenchmark(Benchmark):
    STRUCTURES = DatalakeFixture.LAYOUTS

    def setup_trial(self) -> None:
        dataset = BenchmarkDataset.from_environment()
        self._ids = dataset.ids(self.books)
        self._root = BenchmarkPaths.scratch(
            f"datalake-lookup-{self.structure}-{self.books}"
        )
        Directories.delete(self._root)
        DatalakeFixture.ingest_as_crawled(
            self.structure, self._root, self._ids, dataset, DatalakeFixture.CRAWL_START
        )
        self._datalake = DatalakeFixture.datalake(self.structure, self._root)
        for book_id in self._ids:
            self._require_stored(book_id)

    @timed_operation(MICROSECONDS)
    def lookup_time(self) -> Optional[StoredPaths]:
        return self._datalake.paths_of(self._ids[random.randrange(len(self._ids))])

    def teardown_trial(self) -> None:
        Directories.delete(self._root)

    def _require_stored(self, book_id: int) -> None:
        paths = self._datalake.paths_of(book_id)
        Check.require(
            paths is not None and paths.header.exists() and paths.body.exists(),
            f"book {book_id} not found",
        )
