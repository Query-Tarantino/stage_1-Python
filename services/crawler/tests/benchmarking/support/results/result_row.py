from __future__ import annotations

import math
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class ResultRow:
    LANGUAGE: ClassVar[str] = "python"
    CSV_HEADER: ClassVar[str] = "language,structure,metric,n_books,value,error,unit"
    # error is the half-width of this confidence interval of the mean of the samples
    # (SPEC §11)
    CONFIDENCE: ClassVar[float] = 0.95

    structure: str
    metric: str
    books: int
    value: float
    error: float
    unit: str

    @staticmethod
    def exact(
        structure: str, metric: str, books: int, value: float, unit: str
    ) -> ResultRow:
        return ResultRow(structure, metric, books, value, 0, unit)

    @staticmethod
    def sample(
        structure: str, metric: str, books: int, value: float, unit: str
    ) -> ResultRow:
        return ResultRow(structure, metric, books, value, math.nan, unit)

    @staticmethod
    def parse(csv_line: str) -> ResultRow:
        fields = csv_line.split(",")
        return ResultRow(
            fields[1],
            fields[2],
            int(fields[3]),
            float(fields[4]),
            float(fields[5]) if fields[5] else math.nan,
            fields[6],
        )

    def csv_line(self) -> str:
        error = "" if math.isnan(self.error) else self._decimal(self.error)
        return ",".join(
            [
                self.LANGUAGE,
                self.structure,
                self.metric,
                str(self.books),
                self._decimal(self.value),
                error,
                self.unit,
            ]
        )

    @staticmethod
    def _decimal(number: float) -> str:
        return f"{number:.3f}"
