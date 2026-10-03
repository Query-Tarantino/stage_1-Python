from __future__ import annotations

import queue
from collections import deque
from concurrent.futures import Future
from itertools import islice
from typing import Deque, Dict, List, Optional, Set, Tuple

from tarantino_control.model.next_step import NextStep
from tarantino_control.model.outcome import Outcome
from tarantino_control.model.step_report import StepReport
from tarantino_control.ports.control_state_store import ControlStateStore
from tarantino_control.ports.crawler import Crawler
from tarantino_control.ports.indexer import Indexer


class ControlPipeline:
    MISSING_OUTCOME = Outcome.failure("no outcome from the indexer")

    def __init__(
        self,
        state: ControlStateStore,
        crawler: Crawler,
        indexer: Indexer,
        candidates: List[int],
        parallel_downloads: int,
        index_batch: int,
    ):
        self.state = state
        self.crawler = crawler
        self.indexer = indexer
        self.candidates = candidates
        self.parallel_downloads = parallel_downloads
        self.index_batch = index_batch
        self._downloaded: Dict[int, None] = dict.fromkeys(state.downloaded())
        indexed = set(state.indexed())
        self._to_index: Deque[int] = deque(
            book_id for book_id in self._downloaded if book_id not in indexed
        )
        self._started: Set[int] = set()
        self._finished: queue.SimpleQueue[Tuple[int, Future]] = queue.SimpleQueue()
        self._running = 0
        self._next_candidate = 0

    def run_step(self) -> StepReport:
        self._start_downloads()
        if len(self._to_index) >= self.index_batch or (
            self._to_index and self._running == 0
        ):
            batch = list(islice(self._to_index, self.index_batch))
            return StepReport(NextStep.index(batch), self._indexed(batch))
        if self._running > 0:
            book_id, download = self._finished.get()
            return StepReport(
                NextStep.download(book_id), self._stored(book_id, download)
            )
        return StepReport(NextStep.idle(), Outcome.success("nothing left to do"))

    def _start_downloads(self) -> None:
        while self._running < self.parallel_downloads:
            candidate = self._pending_candidate()
            if candidate is None:
                return
            self._start(candidate)

    def _start(self, book_id: int) -> None:
        try:
            download = self.crawler.ingest(book_id)
        except Exception as error:
            download = Future()
            download.set_exception(error)
        self._started.add(book_id)
        self._running += 1
        download.add_done_callback(lambda done: self._finished.put((book_id, done)))

    def _pending_candidate(self) -> Optional[int]:
        while self._next_candidate < len(self.candidates) and self._is_done(
            self.candidates[self._next_candidate]
        ):
            self._next_candidate += 1
        if self._next_candidate < len(self.candidates):
            return self.candidates[self._next_candidate]
        return None

    def _is_done(self, book_id: int) -> bool:
        return book_id in self._downloaded or book_id in self._started

    def _stored(self, book_id: int, download: Future) -> Outcome:
        self._running -= 1
        try:
            outcome = download.result().store()
        except Exception as error:
            return self._failed(error)
        if outcome.succeeded:
            self.state.mark_downloaded(book_id)
            self._downloaded[book_id] = None
            self._to_index.append(book_id)
        return outcome

    def _indexed(self, batch: List[int]) -> Outcome:
        for _ in batch:
            self._to_index.popleft()
        try:
            outcomes = self.indexer.index(batch)
        except Exception as error:
            return self._failed(error)
        for book_id in batch:
            if self._outcome_of(book_id, outcomes).succeeded:
                self.state.mark_indexed(book_id)
        if len(batch) == 1:
            return self._outcome_of(batch[0], outcomes)
        return self._summary(batch, outcomes)

    @classmethod
    def _summary(cls, batch: List[int], outcomes: Dict[int, Outcome]) -> Outcome:
        indexed = sum(
            1 for book_id in batch if cls._outcome_of(book_id, outcomes).succeeded
        )
        if indexed == len(batch):
            return Outcome.success(f"{indexed} indexed")
        return Outcome.failure(f"{indexed} indexed, {len(batch) - indexed} skipped")

    @classmethod
    def _outcome_of(cls, book_id: int, outcomes: Dict[int, Outcome]) -> Outcome:
        return outcomes.get(book_id, cls.MISSING_OUTCOME)

    @staticmethod
    def _failed(error: Exception) -> Outcome:
        return Outcome.failure(f"failed, {type(error).__name__}: {error}")
