from concurrent.futures import Future
from typing import Callable, Dict, List

import pytest

from tarantino_control.commands.control_pipeline import ControlPipeline
from tarantino_control.model.next_step import NextStep
from tarantino_control.model.outcome import Outcome
from tarantino_control.ports.control_state_store import ControlStateStore
from tarantino_control.ports.crawler import Crawler, Download
from tarantino_control.ports.indexer import Indexer

MISSING_BOOK = 404
ONE_AT_A_TIME = 1
BOOK_BY_BOOK = 1
DEFAULT_BATCH = 100


def completed(download: Download) -> Future:
    future = Future()
    future.set_result(download)
    return future


class Storing(Download):
    def __init__(self, store: Callable[[], Outcome]):
        self._store = store

    def store(self) -> Outcome:
        return self._store()


class RecordingCrawler(Crawler):
    # Downloads that finish at once, in the order they start; a download runs until the
    # pipeline stores it
    def __init__(self):
        self.started: List[int] = []
        self.stored = 0
        self.most_running = 0

    def ingest(self, book_id: int) -> Future:
        self.started.append(book_id)
        self.most_running = max(self.most_running, len(self.started) - self.stored)
        return completed(Storing(lambda: self._store(book_id)))

    def _store(self, book_id: int) -> Outcome:
        self.stored += 1
        if book_id == MISSING_BOOK:
            return Outcome.failure("not found")
        return Outcome.success("stored")


class RecordingIndexer(Indexer):
    def __init__(self):
        self.batches: List[List[int]] = []

    def index(self, book_ids: List[int]) -> Dict[int, Outcome]:
        self.batches.append(list(book_ids))
        return {
            book_id: (
                Outcome.failure("not found")
                if book_id == MISSING_BOOK
                else Outcome.success("indexed")
            )
            for book_id in book_ids
        }


class InMemoryState(ControlStateStore):
    def __init__(self):
        self._downloaded: Dict[int, None] = {}
        self._indexed: Dict[int, None] = {}
        self.reads = 0

    def downloaded(self) -> List[int]:
        self.reads += 1
        return list(self._downloaded)

    def indexed(self) -> List[int]:
        return list(self._indexed)

    def mark_downloaded(self, book_id: int) -> None:
        self._downloaded[book_id] = None

    def mark_indexed(self, book_id: int) -> None:
        self._indexed[book_id] = None


@pytest.fixture
def state() -> InMemoryState:
    return InMemoryState()


@pytest.fixture
def crawler() -> RecordingCrawler:
    return RecordingCrawler()


@pytest.fixture
def indexer() -> RecordingIndexer:
    return RecordingIndexer()


def steps(pipeline: ControlPipeline) -> List[NextStep]:
    taken = []
    while True:
        report = pipeline.run_step()
        if report.idle():
            return taken
        taken.append(report.step)


def test_one_at_a_time_downloads_then_indexes_each_candidate_and_skips_failures(
    state, crawler, indexer
):
    pipeline = ControlPipeline(
        state, crawler, indexer, [1, MISSING_BOOK, 2], ONE_AT_A_TIME, BOOK_BY_BOOK
    )

    assert steps(pipeline) == [
        NextStep.download(1),
        NextStep.index([1]),
        NextStep.download(MISSING_BOOK),
        NextStep.download(2),
        NextStep.index([2]),
    ]
    assert state.indexed() == [1, 2]


def test_indexes_in_batches_and_the_last_partial_batch_when_nothing_is_left_to_download(
    state, crawler, indexer
):
    pipeline = ControlPipeline(state, crawler, indexer, [1, 2, 3], ONE_AT_A_TIME, 2)

    assert steps(pipeline) == [
        NextStep.download(1),
        NextStep.download(2),
        NextStep.index([1, 2]),
        NextStep.download(3),
        NextStep.index([3]),
    ]
    assert indexer.batches == [[1, 2], [3]]
    assert state.indexed() == [1, 2, 3]


def test_downloads_up_to_the_parallel_downloads_at_once_started_in_candidates_order(
    state, crawler, indexer
):
    pipeline = ControlPipeline(
        state, crawler, indexer, [1, 2, 3, 4, 5], 3, DEFAULT_BATCH
    )

    pipeline.run_step()
    assert crawler.started == [1, 2, 3]

    steps(pipeline)
    assert crawler.started == [1, 2, 3, 4, 5]
    assert crawler.most_running == 3
    assert state.indexed() == [1, 2, 3, 4, 5]


def test_stores_marks_and_queues_books_in_the_order_their_downloads_finish(
    state, indexer
):
    slow_download = Future()

    class FirstFinishesLast(Crawler):
        def ingest(self, book_id: int) -> Future:
            if book_id == 1:
                return slow_download
            return completed(Storing(self._store_and_finish_the_slow_one))

        @staticmethod
        def _store_and_finish_the_slow_one() -> Outcome:
            slow_download.set_result(Storing(lambda: Outcome.success("stored")))
            return Outcome.success("stored")

    pipeline = ControlPipeline(state, FirstFinishesLast(), indexer, [1, 2], 2, 2)

    assert steps(pipeline) == [
        NextStep.download(2),
        NextStep.download(1),
        NextStep.index([2, 1]),
    ]
    assert state.downloaded() == [2, 1]


def test_starts_the_next_downloads_before_indexing_a_batch(state, crawler, indexer):
    started_when_indexing = []

    class Watched(Indexer):
        def index(self, book_ids: List[int]) -> Dict[int, Outcome]:
            started_when_indexing.append(list(crawler.started))
            return indexer.index(book_ids)

    steps(ControlPipeline(state, crawler, Watched(), [1, 2, 3], 2, BOOK_BY_BOOK))

    assert started_when_indexing[0] == [1, 2, 3]


def test_an_unexpected_download_error_fails_only_its_book(state, crawler, indexer):
    class BrokenForOne(Crawler):
        def ingest(self, book_id: int) -> Future:
            if book_id != 1:
                return crawler.ingest(book_id)
            future = Future()
            future.set_exception(RuntimeError("bug in the crawler"))
            return future

    pipeline = ControlPipeline(state, BrokenForOne(), indexer, [1, 2], 1, BOOK_BY_BOOK)

    first = pipeline.run_step()
    assert first.step == NextStep.download(1)
    assert first.outcome == Outcome.failure("failed, RuntimeError: bug in the crawler")
    assert steps(pipeline) == [NextStep.download(2), NextStep.index([2])]
    assert state.downloaded() == [2]


def test_an_error_starting_a_download_fails_only_its_book(state, crawler, indexer):
    # Such as the datalake failing while looking up whether the book is stored
    class BrokenLookup(Crawler):
        def ingest(self, book_id: int) -> Future:
            if book_id == 1:
                raise OSError("datalake unreadable")
            return crawler.ingest(book_id)

    pipeline = ControlPipeline(state, BrokenLookup(), indexer, [1, 2], 1, BOOK_BY_BOOK)

    first = pipeline.run_step()
    assert first.step == NextStep.download(1)
    assert first.outcome == Outcome.failure("failed, OSError: datalake unreadable")
    assert steps(pipeline) == [NextStep.download(2), NextStep.index([2])]
    assert state.downloaded() == [2]


def test_an_unexpected_indexing_error_fails_its_batch_without_marking_its_books(
    state, crawler, indexer
):
    state.mark_downloaded(1)
    state.mark_downloaded(2)

    class Interrupted(Indexer):
        def index(self, book_ids: List[int]) -> Dict[int, Outcome]:
            raise OSError("interrupted while flushing")

    pipeline = ControlPipeline(state, crawler, Interrupted(), [], 1, DEFAULT_BATCH)

    report = pipeline.run_step()
    assert report.step == NextStep.index([1, 2])
    assert report.outcome == Outcome.failure(
        "failed, OSError: interrupted while flushing"
    )
    assert state.indexed() == []
    assert pipeline.run_step().idle()

    next_run = ControlPipeline(state, crawler, indexer, [], 1, DEFAULT_BATCH)
    assert next_run.run_step().step == NextStep.index([1, 2])


def test_resumes_by_indexing_books_downloaded_before_an_interruption(
    state, crawler, indexer
):
    state.mark_downloaded(7)
    pipeline = ControlPipeline(
        state, crawler, indexer, [], ONE_AT_A_TIME, DEFAULT_BATCH
    )

    assert pipeline.run_step().step == NextStep.index([7])


def test_marks_the_books_of_a_batch_that_succeed_and_goes_on_without_the_ones_that_fail(
    state, crawler, indexer
):
    state.mark_downloaded(MISSING_BOOK)
    state.mark_downloaded(8)
    pipeline = ControlPipeline(
        state, crawler, indexer, [], ONE_AT_A_TIME, DEFAULT_BATCH
    )

    assert pipeline.run_step().outcome == Outcome.failure("1 indexed, 1 skipped")
    assert state.indexed() == [8]
    assert pipeline.run_step().idle()


def test_skips_candidates_already_downloaded_or_repeated(state, crawler, indexer):
    state.mark_downloaded(1)
    state.mark_indexed(1)
    pipeline = ControlPipeline(state, crawler, indexer, [1, 2, 1, 2], 2, BOOK_BY_BOOK)

    assert steps(pipeline) == [NextStep.download(2), NextStep.index([2])]
    assert crawler.started == [2]


def test_reads_the_state_once_whatever_the_number_of_steps(state, crawler, indexer):
    steps(
        ControlPipeline(
            state, crawler, indexer, [1, 2, 3, 4, 5], ONE_AT_A_TIME, BOOK_BY_BOOK
        )
    )

    assert state.reads == 1
