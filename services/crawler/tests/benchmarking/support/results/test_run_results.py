import math

import pytest

from services.crawler.tests.benchmarking.support.harness.iterations import P99, SCORE
from services.crawler.tests.benchmarking.support.processes.configuration import (
    Configuration,
)
from services.crawler.tests.benchmarking.support.processes.process_result import (
    ProcessResult,
)
from services.crawler.tests.benchmarking.support.results.metric import Metric
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow
from services.crawler.tests.benchmarking.support.results.run_results import (
    RunResults,
)

QUERY_TIME = Configuration("module:QueryTimeBenchmark", "query_time", "json", 100)
METRICS = {"query_time": Metric.as_measured("query_time", "µs/query")}


def process(samples=None, exact_rows=(), sample_rows=()) -> ProcessResult:
    return ProcessResult(samples or {}, list(exact_rows), list(sample_rows))


def test_joins_the_samples_of_every_process_of_a_configuration():
    results = RunResults()
    results.add(QUERY_TIME, process({SCORE: [10.0, 12.0], P99: [30.0, 30.0]}))
    results.add(QUERY_TIME, process({SCORE: [14.0], P99: [33.0]}))

    query_time, p99 = results.rows(METRICS)

    assert (query_time.metric, query_time.value) == ("query_time", 12.0)
    assert query_time.error == pytest.approx(4.968, abs=1e-3)
    assert (p99.metric, p99.value, p99.unit) == ("query_time_p99", 31.0, "µs/query")


def test_keeps_one_row_per_exact_measure_whatever_the_number_of_processes():
    term_count = ResultRow.exact("folders", "term_count", 100, 106_410, "terms")
    results = RunResults()
    for _ in range(3):
        results.add(QUERY_TIME, process(exact_rows=[term_count]))

    assert results.rows({}) == [term_count]


def test_gives_recorded_samples_as_their_mean_and_95_confidence_half_width():
    results = RunResults()
    for value in (10.0, 12.0, 14.0):
        sample = ResultRow.sample("json", "build_memory", 100, value, "bytes")
        results.add(QUERY_TIME, process(sample_rows=[sample]))

    (mean,) = results.rows({})

    assert mean.value == 12.0
    assert mean.error == pytest.approx(4.968, abs=1e-3)


def test_cannot_compute_the_error_of_a_single_sample():
    results = RunResults()
    results.add(QUERY_TIME, process({SCORE: [2.9]}))

    assert math.isnan(results.rows(METRICS)[0].error)


def test_gives_nothing_when_nothing_was_measured():
    assert RunResults().rows(METRICS) == []
