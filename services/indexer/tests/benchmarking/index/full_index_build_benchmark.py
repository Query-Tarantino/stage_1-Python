from __future__ import annotations

from services.crawler.tests.benchmarking.support.environment.heap import Heap
from services.crawler.tests.benchmarking.support.harness.benchmark import (
    Benchmark,
    whole_run,
)
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow
from services.crawler.tests.benchmarking.support.validation.check import Check
from services.indexer.tests.benchmarking.support.benchmark_store import BenchmarkStore
from services.indexer.tests.benchmarking.support.index_fixture import IndexFixture
from services.indexer.tests.benchmarking.support.prebuilt_indexes import (
    PrebuiltIndexes,
)


class FullIndexBuildBenchmark(Benchmark):
    STRUCTURES = ("json", "folders", "mongo")
    WARM_UP_BOOKS = 100
    BUILD_MEMORY_SAMPLES = 3

    def setup_trial(self) -> None:
        self._fixture = IndexFixture.from_environment()
        self._store = BenchmarkStore.for_index(
            self.structure, f"index-build-{self.structure}-{self.books}"
        )
        self._ids = self._fixture.dataset.ids(self.books)
        self._reference_term_count = self._term_count_of_the_books()
        self._warm_up()

    def _warm_up(self) -> None:
        for book_id in self._ids:
            self._fixture.dataset.raw_text(book_id)
        warm_up = BenchmarkStore.for_index(
            self.structure, f"index-build-warmup-{self.structure}"
        )
        warm_up.clear()
        self._fixture.index(
            warm_up.inverted_index(), self._fixture.dataset.ids(self.WARM_UP_BOOKS)
        )
        warm_up.clear()

    def setup_iteration(self, measured: bool) -> None:
        self._store.clear()

    @whole_run(warm_up=0)
    def full_build_time(self) -> None:
        self._fixture.index(self._store.inverted_index(), self._ids)

    def teardown_trial(self) -> None:
        footprint = self._store.footprint()
        Check.require(
            footprint.terms == self._reference_term_count,
            f"{self.structure} holds {footprint.terms} terms instead of the"
            f" {self._reference_term_count} of the books",
        )
        self.record_exact(
            [
                ResultRow.exact(
                    self.structure, "disk_usage", self.books, footprint.bytes, "bytes"
                ),
                ResultRow.exact(
                    self.structure,
                    "disk_allocated",
                    self.books,
                    footprint.allocated_bytes,
                    "bytes",
                ),
                ResultRow.exact(
                    self.structure, "term_count", self.books, footprint.terms, "terms"
                ),
            ]
        )
        for _ in range(self.BUILD_MEMORY_SAMPLES):
            self._store.clear()
            self.record_sample(
                ResultRow.sample(
                    self.structure,
                    "build_memory",
                    self.books,
                    self._build_memory(),
                    "bytes",
                )
            )
        self._store.clear()

    def _term_count_of_the_books(self) -> int:
        cached = PrebuiltIndexes.file(f"term-count-{self.books}.txt")
        if cached.exists():
            return int(cached.read_text(encoding="utf-8"))
        term_count = self._fixture.vocabulary_size(self._ids)
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(str(term_count), encoding="utf-8")
        return term_count

    def _build_memory(self) -> int:
        def add_books():
            inverted_index = self._store.inverted_index()
            self._fixture.add(inverted_index, self._ids)
            return inverted_index

        retained, _ = Heap.retained_by(add_books)
        return retained
