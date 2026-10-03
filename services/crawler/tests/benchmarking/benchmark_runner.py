from __future__ import annotations

from typing import List

from services.crawler.tests.benchmarking.datalake.datalake_lookup_benchmark import (
    DatalakeLookupBenchmark,
)
from services.crawler.tests.benchmarking.datalake.datalake_write_benchmark import (
    DatalakeWriteBenchmark,
)
from services.crawler.tests.benchmarking.datalake.new_books_detection_benchmark import (
    NewBooksDetectionBenchmark,
)
from services.crawler.tests.benchmarking.support.datalake.datalake_fixture import (
    DatalakeFixture,
)
from services.crawler.tests.benchmarking.support.datalake.recovery_scenario import (
    RecoveryScenario,
)
from services.crawler.tests.benchmarking.support.dataset.benchmark_dataset import (
    BenchmarkDataset,
)
from services.crawler.tests.benchmarking.support.environment.benchmark_options import (
    BenchmarkOptions,
)
from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)
from services.crawler.tests.benchmarking.support.files.directories import Directories
from services.crawler.tests.benchmarking.support.files.results_file import ResultsFile
from services.crawler.tests.benchmarking.support.processes.benchmark_passes import (
    BenchmarkPasses,
)
from services.crawler.tests.benchmarking.support.results.metric import Metric
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow

SERVICE = "crawler"
BENCHMARKS = [
    DatalakeLookupBenchmark,
    DatalakeWriteBenchmark,
    NewBooksDetectionBenchmark,
]
METRICS = {
    "write_throughput": Metric.books_per_second("write_throughput"),
    "lookup_time": Metric.as_measured("lookup_time", "µs/op"),
    "new_books_detection_time": Metric.as_measured("new_books_detection_time", "ms"),
}
RECOVERY_BOOKS = 100


def main() -> None:
    results = BenchmarkPasses(
        SERVICE, BENCHMARKS, BenchmarkOptions.from_environment()
    ).run()
    rows = results.rows(METRICS) + recovery_rows()
    print(f"Results written to {ResultsFile.write(SERVICE, rows)}")


def recovery_rows() -> List[ResultRow]:
    dataset = BenchmarkDataset.from_environment()
    return [
        row
        for layout in DatalakeFixture.LAYOUTS
        for row in layout_recovery_rows(layout, dataset)
    ]


def layout_recovery_rows(layout: str, dataset: BenchmarkDataset) -> List[ResultRow]:
    root = BenchmarkPaths.scratch(f"datalake-recovery-{layout}")
    Directories.delete(root)
    outcome = RecoveryScenario(layout, root, dataset).run(dataset.ids(RECOVERY_BOOKS))
    Directories.delete(root)
    return [
        ResultRow.exact(
            layout, "recovery_ok", RECOVERY_BOOKS, int(outcome.recovered), "0 or 1"
        ),
        ResultRow.exact(
            layout,
            "recovery_leftover_files",
            RECOVERY_BOOKS,
            outcome.leftover_files,
            "files",
        ),
    ]


if __name__ == "__main__":
    main()
