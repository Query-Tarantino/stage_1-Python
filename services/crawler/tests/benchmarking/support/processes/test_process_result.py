import math

from services.crawler.tests.benchmarking.support.harness.iterations import SCORE
from services.crawler.tests.benchmarking.support.processes.configuration import (
    Configuration,
)
from services.crawler.tests.benchmarking.support.processes.process_result import (
    ProcessResult,
)
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow


def test_reaches_the_run_unchanged_unknown_errors_included():
    sample = ResultRow.sample("json", "index_memory", 100, 49_157_986.4, "bytes")
    exact = ResultRow.exact("book", "file_count", 100, 200, "files")
    result = ProcessResult({SCORE: [0.123456789, 2.5]}, [exact], [sample])

    read = ProcessResult.from_json(result.to_json())

    assert read.samples == result.samples
    assert read.exact_rows == [exact]
    assert read.sample_rows[0].value == sample.value
    assert math.isnan(read.sample_rows[0].error)


def test_names_a_configuration_by_its_benchmark_class_and_reads_it_back():
    configuration = Configuration(
        "services.example:QueryTimeBenchmark", "query_time", "folders", 300
    )

    assert str(configuration) == "QueryTimeBenchmark.query_time folders 300"
    assert Configuration.from_json(configuration.to_json()) == configuration
