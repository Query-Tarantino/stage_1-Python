from __future__ import annotations

from services.crawler.tests.benchmarking.support.harness.benchmark import (
    Benchmark,
    whole_run,
)
from services.indexer.tests.benchmarking.support.benchmark_store import BenchmarkStore
from services.indexer.tests.benchmarking.support.index_fixture import IndexFixture


class MetadataInsertionBenchmark(Benchmark):
    STRUCTURES = ("sqlite", "mongo")

    def setup_trial(self) -> None:
        self._fixture = IndexFixture.from_environment()
        self._store = BenchmarkStore.for_metadata(
            self.structure, f"metadata-insert-{self.structure}-{self.books}"
        )
        self._books = self._fixture.books(self._fixture.dataset.ids(self.books))

    def setup_iteration(self, measured: bool) -> None:
        self._store.clear()

    @whole_run()
    def bulk_insertion_time(self) -> None:
        self._fixture.save(self._store.metadata(), self._books)

    def teardown_trial(self) -> None:
        self._store.clear()
