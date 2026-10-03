import math

import pytest

from services.crawler.tests.benchmarking.support.results.metric import Metric
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow


def test_keeps_measured_scores_and_errors_as_they_are():
    row = Metric.as_measured("lookup_time", "µs/op").row("book", 100, 0.43, 0.08)

    assert row == ResultRow("book", "lookup_time", 100, 0.43, 0.08, "µs/op")


def test_turns_the_time_to_write_n_books_into_throughput_keeping_the_relative_error():
    row = Metric.books_per_second("write_throughput").row("batch", 100, 250, 25)

    assert row.value == pytest.approx(400)
    assert row.error == pytest.approx(40)
    assert row.unit == "books/s"


def test_divides_the_time_of_a_run_by_its_books():
    row = Metric.per_book("incremental_update_time", 10).row("json", 2000, 2556, 120)

    assert row.value == pytest.approx(255.6)
    assert row.error == pytest.approx(12)
    assert row.unit == "ms/book"


def test_keeps_an_unknown_error_unknown():
    row = Metric.as_measured("query_time", "µs/query").row("json", 100, 2.9, math.nan)

    assert math.isnan(row.error)


def test_names_a_statistic_of_the_same_samples_with_the_same_unit():
    p99 = Metric.as_measured("query_time", "µs/query").named("query_time_p99")

    assert p99.row("json", 100, 10.7, 0.3) == ResultRow(
        "json", "query_time_p99", 100, 10.7, 0.3, "µs/query"
    )
