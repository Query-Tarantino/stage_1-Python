from __future__ import annotations

from services.crawler.tests.benchmarking.support.environment.benchmark_options import (
    BenchmarkOptions,
)
from services.crawler.tests.benchmarking.support.files.results_file import ResultsFile
from services.crawler.tests.benchmarking.support.processes.benchmark_passes import (
    BenchmarkPasses,
)
from services.crawler.tests.benchmarking.support.results.metric import Metric
from services.indexer.tests.benchmarking.index.full_index_build_benchmark import (
    FullIndexBuildBenchmark,
)
from services.indexer.tests.benchmarking.index.incremental_update_benchmark import (
    IncrementalUpdateBenchmark,
)
from services.indexer.tests.benchmarking.metadata.metadata_insertion_benchmark import (
    MetadataInsertionBenchmark,
)
from services.indexer.tests.benchmarking.support.prebuilt_indexes import (
    PrebuiltIndexes,
)

SERVICE = "indexer"
BENCHMARKS = [
    FullIndexBuildBenchmark,
    IncrementalUpdateBenchmark,
    MetadataInsertionBenchmark,
]
METRICS = {
    "full_build_time": Metric.as_measured("full_build_time", "ms"),
    "incremental_update_time": Metric.per_book(
        "incremental_update_time", IncrementalUpdateBenchmark.BOOKS_FLUSHED_ONE_BY_ONE
    ),
    "batch_update_time": Metric.per_book(
        "batch_update_time", IncrementalUpdateBenchmark.BOOKS_FLUSHED_TOGETHER
    ),
    "bulk_insertion_time": Metric.as_measured("bulk_insertion_time", "ms"),
}


def main() -> None:
    PrebuiltIndexes.delete_all()
    try:
        results = BenchmarkPasses(
            SERVICE, BENCHMARKS, BenchmarkOptions.from_environment()
        ).run()
        print(f"Results written to {ResultsFile.write(SERVICE, results.rows(METRICS))}")
    finally:
        PrebuiltIndexes.delete_all()


if __name__ == "__main__":
    main()
