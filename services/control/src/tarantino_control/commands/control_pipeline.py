from __future__ import annotations

from typing import Callable, Collection, List, Optional, Set

from tarantino_control.model.next_step import Action, NextStep
from tarantino_control.model.outcome import Outcome
from tarantino_control.model.step_report import StepReport
from tarantino_control.ports.control_state_store import ControlStateStore
from tarantino_control.ports.crawler import Crawler
from tarantino_control.ports.indexer import Indexer


class ControlPipeline:
    def __init__(
        self,
        state: ControlStateStore,
        crawler: Crawler,
        indexer: Indexer,
        candidates: List[int],
    ):
        self.state = state
        self.crawler = crawler
        self.indexer = indexer
        self.candidates = candidates
        self.failed: Set[int] = set()

    def next_step(self) -> NextStep:
        downloaded = self.state.downloaded()
        indexed = self.state.indexed()

        first_index = self._first_pending(downloaded, indexed)
        if first_index is not None:
            return NextStep.index(first_index)

        first_download = self._first_pending(self.candidates, downloaded)
        if first_download is not None:
            return NextStep.download(first_download)

        return NextStep.idle()

    def run_step(self) -> StepReport:
        step = self.next_step()
        return StepReport(step, self._outcome(step))

    def _first_pending(self, ids: Collection[int], done: Set[int]) -> Optional[int]:
        for book_id in ids:
            if book_id not in done and book_id not in self.failed:
                return book_id
        return None

    def _outcome(self, step: NextStep) -> Outcome:
        if step.action == Action.INDEX:
            return self._register(step, self.indexer.index, self.state.mark_indexed)
        elif step.action == Action.DOWNLOAD:
            return self._register(step, self.crawler.ingest, self.state.mark_downloaded)
        elif step.action == Action.IDLE:
            return Outcome.success("nothing left to do")
        else:
            raise ValueError(f"Unknown action {step.action}")

    def _register(
        self,
        step: NextStep,
        operation: Callable[[int], Outcome],
        mark_done: Callable[[int], None],
    ) -> Outcome:
        outcome = self._attempt(operation, step.book_id)
        if outcome.succeeded:
            mark_done(step.book_id)
        else:
            self.failed.add(step.book_id)
        return outcome

    @staticmethod
    def _attempt(operation: Callable[[int], Outcome], book_id: int) -> Outcome:
        # An unexpected error fails only this book, like any other failure, instead
        # of stopping the run at the same book every time it restarts.
        try:
            return operation(book_id)
        except Exception as e:
            return Outcome.failure(f"failed, {type(e).__name__}: {e}")
