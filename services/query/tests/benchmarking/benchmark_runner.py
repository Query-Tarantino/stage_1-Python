from __future__ import annotations

from services.crawler.tests.benchmarking.support.environment.benchmark_options import (
    BenchmarkOptions,
)
from services.crawler.tests.benchmarking.support.files.results_file import ResultsFile
from services.crawler.tests.benchmarking.support.processes.benchmark_passes import (
    BenchmarkPasses,
)
from services.crawler.tests.benchmarking.support.results.metric import Metric
from services.indexer.tests.benchmarking.support.prebuilt_indexes import (
    PrebuiltIndexes,
)
from services.query.tests.benchmarking.index_open_benchmark import IndexOpenBenchmark
from services.query.tests.benchmarking.metadata_query_benchmark import (
    MetadataQueryBenchmark,
)
from services.query.tests.benchmarking.query_time_benchmark import QueryTimeBenchmark

SERVICE = "query"
BENCHMARKS = [IndexOpenBenchmark, MetadataQueryBenchmark, QueryTimeBenchmark]
METRICS = {
    "index_open_time": Metric.as_measured("index_open_time", "ms"),
    "book_by_id_time": Metric.as_measured("book_by_id_time", "µs/op"),
    "books_by_author_time": Metric.as_measured("books_by_author_time", "µs/op"),
    "query_time": Metric.as_measured("query_time", QueryTimeBenchmark.QUERY_TIME_UNIT),
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
