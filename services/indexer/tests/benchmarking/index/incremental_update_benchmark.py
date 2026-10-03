from __future__ import annotations

from services.crawler.tests.benchmarking.support.dataset.benchmark_dataset import (
    BenchmarkDataset,
)
from services.crawler.tests.benchmarking.support.harness.benchmark import (
    Benchmark,
    whole_run,
)
from services.indexer.tests.benchmarking.support.benchmark_store import BenchmarkStore
from services.indexer.tests.benchmarking.support.index_fixture import IndexFixture
from services.indexer.tests.benchmarking.support.prebuilt_indexes import (
    PrebuiltIndexes,
)


class IncrementalUpdateBenchmark(Benchmark):
    STRUCTURES = ("json", "folders", "mongo")
    # Flushing after every book is far slower (folders rewrites every term file of
    # each book), so fewer books
    BOOKS_FLUSHED_ONE_BY_ONE = 10
    BOOKS_FLUSHED_TOGETHER = BenchmarkDataset.NEW_BOOKS

    def setup_trial(self) -> None:
        self._fixture = IndexFixture.from_environment()
        self._snapshot = PrebuiltIndexes.of(self.structure, self.books, self._fixture)
        self._store = PrebuiltIndexes.working_copy_of(
            self._snapshot, self.structure, self.books
        )
        self._new_ids = self._fixture.dataset.new_ids()
        self._books_flushed_one_by_one = self._new_ids[: self.BOOKS_FLUSHED_ONE_BY_ONE]
        self._touched_terms = {
            term for book_id in self._new_ids for term in self._fixture.terms(book_id)
        }
        self._warm_up()

    def _warm_up(self) -> None:
        # The same code instead of a whole warm-up run (SPEC §11): the first new books
        # indexed into an empty index one by one, which creates their term files, and
        # then together, which merges them
        warm_up = BenchmarkStore.for_index(
            self.structure, f"index-update-warmup-{self.structure}"
        )
        warm_up.clear()
        inverted_index = warm_up.inverted_index()
        for book_id in self._books_flushed_one_by_one:
            self._fixture.index(inverted_index, [book_id])
        self._fixture.index(warm_up.inverted_index(), self._books_flushed_one_by_one)
        warm_up.clear()

    def setup_iteration(self, measured: bool) -> None:
        # Every run starts from the prebuilt index, with the terms of the new books put
        # back (SPEC §11), and opens it before timing, as a running control layer has
        # it open: otherwise json's loading would be spread over 10 books in one method
        # and over 100 in the other. Loading is measured by index_open_time.
        self._store.restore_terms_from(self._snapshot, self._touched_terms)
        self._inverted_index = self._store.inverted_index()
        self._inverted_index.open()

    @whole_run(warm_up=0)
    def incremental_update_time(self) -> None:
        # As the control layer indexes with K = 1 (SPEC §9): an open index, flushed
        # after every book
        for book_id in self._books_flushed_one_by_one:
            self._fixture.index(self._inverted_index, [book_id])

    @whole_run(warm_up=0)
    def batch_update_time(self) -> None:
        # As the control layer indexes with the default K = 100: an open index,
        # flushed once
        self._fixture.index(self._inverted_index, self._new_ids)
