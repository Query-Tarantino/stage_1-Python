from __future__ import annotations

from typing import Callable, Iterable, List, Tuple, TypeVar

from services.crawler.tests.benchmarking.support.harness.iterations import (
    MILLISECONDS,
    Iterations,
    SampledOperations,
    TimedOperations,
    WholeRuns,
)
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow

Method = TypeVar("Method", bound=Callable)
ITERATIONS = "iterations"


class Benchmark:
    # One configuration of a benchmark, run in a process of its own: a structure of
    # STRUCTURES and a size of SIZES (SPEC §11). Its measured methods are marked with
    # whole_run, timed_operation or sampled_operation, and, as JMH's @Setup and
    # @TearDown methods, the hooks run around the trial and around each iteration,
    # untimed.
    STRUCTURES: Tuple[str, ...] = ()
    SIZES: Tuple[int, ...] = (100, 300, 1000)

    def __init__(self, structure: str, books: int):
        self.structure = structure
        self.books = books
        self.exact_rows: List[ResultRow] = []
        self.sample_rows: List[ResultRow] = []

    @classmethod
    def measured_methods(cls) -> List[str]:
        return [
            name for name, member in vars(cls).items() if hasattr(member, ITERATIONS)
        ]

    def setup_trial(self) -> None:
        pass

    def setup_iteration(self, measured: bool) -> None:
        pass

    def teardown_iteration(self, measured: bool) -> None:
        pass

    def teardown_trial(self) -> None:
        pass

    def record_exact(self, rows: Iterable[ResultRow]) -> None:
        # Measures equal in every process, such as what a run leaves on disk: the run
        # keeps the first process's
        self.exact_rows.extend(rows)

    def record_sample(self, row: ResultRow) -> None:
        # A measure taken in every process, such as retained memory: the run gives the
        # mean of every process's samples
        self.sample_rows.append(row)


def whole_run(warm_up: int = 1, measured: int = 3) -> Callable[[Method], Method]:
    # Full builds and updates warm up in setup_trial on a small input instead, with
    # warm_up=0 (SPEC §11)
    return _measured_by(WholeRuns(warm_up, measured))


def timed_operation(unit: int = MILLISECONDS) -> Callable[[Method], Method]:
    return _measured_by(TimedOperations(unit))


def sampled_operation(unit: int = MILLISECONDS) -> Callable[[Method], Method]:
    return _measured_by(SampledOperations(unit))


def iterations_of(method: Callable) -> Iterations:
    return getattr(method, ITERATIONS)


def _measured_by(iterations: Iterations) -> Callable[[Method], Method]:
    def mark(method: Method) -> Method:
        setattr(method, ITERATIONS, iterations)
        return method

    return mark
