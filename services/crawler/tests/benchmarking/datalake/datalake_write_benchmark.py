from __future__ import annotations

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
    whole_run,
)


class DatalakeWriteBenchmark(Benchmark):
    STRUCTURES = DatalakeFixture.LAYOUTS

    def setup_trial(self) -> None:
        self._dataset = BenchmarkDataset.from_environment()
        self._ids = self._dataset.ids(self.books)
        self._root = BenchmarkPaths.scratch(
            f"datalake-write-{self.structure}-{self.books}"
        )

    def setup_iteration(self, measured: bool) -> None:
        Directories.delete(self._root)

    @whole_run()
    def write_throughput(self) -> None:
        # Ingesting the N books as the crawler does, into an empty datalake (SPEC §11)
        DatalakeFixture.ingest_as_crawled(
            self.structure,
            self._root,
            self._ids,
            self._dataset,
            DatalakeFixture.CRAWL_START,
        )

    def teardown_trial(self) -> None:
        self.record_exact(
            DatalakeFixture.footprint(self.structure, self.books, self._root)
        )
        Directories.delete(self._root)
