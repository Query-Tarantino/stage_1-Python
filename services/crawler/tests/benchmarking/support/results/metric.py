from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from services.crawler.tests.benchmarking.support.results.result_row import ResultRow


@dataclass(frozen=True)
class Metric:
    name: str
    unit: str
    # The value of the metric from the mean of the samples and the books of the run
    conversion: Callable[[float, int], float]

    @staticmethod
    def as_measured(name: str, unit: str) -> Metric:
        return Metric(name, unit, lambda score, books: score)

    @staticmethod
    def per_book(name: str, books_per_run: int) -> Metric:
        return Metric(
            name, "ms/book", lambda milliseconds, books: milliseconds / books_per_run
        )

    @staticmethod
    def books_per_second(name: str) -> Metric:
        return Metric(
            name, "books/s", lambda milliseconds, books: books / (milliseconds / 1000)
        )

    def named(self, name: str) -> Metric:
        return Metric(name, self.unit, self.conversion)

    def row(
        self, structure: str, books: int, score: float, score_error: float
    ) -> ResultRow:
        # A value derived from a time keeps the relative error of the time (SPEC §11)
        value = self.conversion(score, books)
        error = abs(value * score_error / score)
        return ResultRow(structure, self.name, books, value, error, self.unit)
