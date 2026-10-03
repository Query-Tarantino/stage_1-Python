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
        self.exact_rows.extend(rows)

    def record_sample(self, row: ResultRow) -> None:
        self.sample_rows.append(row)


def whole_run(warm_up: int = 1, measured: int = 3) -> Callable[[Method], Method]:
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
