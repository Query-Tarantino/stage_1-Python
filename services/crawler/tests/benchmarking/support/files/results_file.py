from __future__ import annotations

from pathlib import Path
from typing import List

from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow


class ResultsFile:

    @staticmethod
    def write(service: str, rows: List[ResultRow]) -> Path:
        file = (
            BenchmarkPaths.benchmarks()
            / "results"
            / f"{ResultRow.LANGUAGE}-{service}.csv"
        )
        file.parent.mkdir(parents=True, exist_ok=True)
        lines = [ResultRow.CSV_HEADER, *(row.csv_line() for row in rows)]
        file.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        return file
