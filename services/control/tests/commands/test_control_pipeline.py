from typing import Set

from tarantino_control.commands.control_pipeline import ControlPipeline
from tarantino_control.model.next_step import Action, NextStep
from tarantino_control.model.outcome import Outcome
from tarantino_control.ports.control_state_store import ControlStateStore
from tarantino_control.ports.crawler import Crawler
from tarantino_control.ports.indexer import Indexer


class InMemoryState(ControlStateStore):
    def __init__(self):
        self._downloaded: Set[int] = set()
        self._indexed: Set[int] = set()

    def mark_downloaded(self, book_id: int) -> None:
        self._downloaded.add(book_id)

    def mark_indexed(self, book_id: int) -> None:
        self._indexed.add(book_id)

    def downloaded(self) -> Set[int]:
        return set(self._downloaded)

    def indexed(self) -> Set[int]:
        return set(self._indexed)


MISSING_BOOK = 404
BROKEN_BOOK = 500


class FakeCrawler(Crawler):
    def ingest(self, book_id: int) -> Outcome:
        if book_id == MISSING_BOOK:
            return Outcome.failure("not found")
        return Outcome.success("stored")


class FakeIndexer(Indexer):
    def index(self, book_id: int) -> Outcome:
        return Outcome.success("indexed")


class BrokenIndexer(Indexer):
    def index(self, book_id: int) -> Outcome:
        if book_id == BROKEN_BOOK:
            raise OSError("cannot write term file")
        return Outcome.success("indexed")


def test_downloads_then_indexes_each_candidate_and_skips_failures():
    state = InMemoryState()
    crawler = FakeCrawler()
    indexer = FakeIndexer()

    pipeline = ControlPipeline(state, crawler, indexer, [1, MISSING_BOOK, 2])

    steps = []
    while True:
        step = pipeline.next_step()
        if step.action == Action.IDLE:
            break
        steps.append(step)
        pipeline.run_step()

    expected_steps = [
        NextStep.download(1),
        NextStep.index(1),
        NextStep.download(MISSING_BOOK),
        NextStep.download(2),
        NextStep.index(2),
    ]

    assert steps == expected_steps
    assert state.indexed() == {1, 2}


def test_resumes_by_indexing_books_downloaded_before_an_interruption():
    state = InMemoryState()
    crawler = FakeCrawler()
    indexer = FakeIndexer()

    state.mark_downloaded(7)
    pipeline = ControlPipeline(state, crawler, indexer, [])

    assert pipeline.next_step() == NextStep.index(7)


def test_an_error_fails_only_its_book_and_the_run_goes_on():
    state = InMemoryState()
    candidates = [1, BROKEN_BOOK, 2]
    pipeline = ControlPipeline(state, FakeCrawler(), BrokenIndexer(), candidates)

    reports = []
    while True:
        report = pipeline.run_step()
        if report.idle():
            break
        reports.append(report)

    failures = [report for report in reports if not report.outcome.succeeded]
    assert [report.step for report in failures] == [NextStep.index(BROKEN_BOOK)]
    assert failures[0].outcome.detail == "failed, OSError: cannot write term file"
    assert state.indexed() == {1, 2}

    next_run = ControlPipeline(state, FakeCrawler(), BrokenIndexer(), candidates)
    assert next_run.next_step() == NextStep.index(BROKEN_BOOK)
