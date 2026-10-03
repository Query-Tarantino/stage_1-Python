import math

from services.crawler.tests.benchmarking.support.results.result_row import ResultRow


def test_writes_the_spec_csv_line_with_three_decimals():
    row = ResultRow("time", "write_throughput", 1000, 812.4, 35.25, "books/s")

    assert row.csv_line() == "python,time,write_throughput,1000,812.400,35.250,books/s"


def test_writes_an_unknown_error_as_an_empty_field():
    row = ResultRow.sample("json", "query_time", 100, 2.958, "µs/query")

    assert row.csv_line() == "python,json,query_time,100,2.958,,µs/query"


def test_exact_rows_have_no_error():
    assert ResultRow.exact("book", "file_count", 100, 200, "files").error == 0


def test_reads_back_the_lines_it_writes():
    row = ResultRow("mongo", "disk_usage", 500, 34_700_000, 0, "bytes")

    assert ResultRow.parse(row.csv_line()) == row
    assert math.isnan(
        ResultRow.parse("python,json,query_time,100,2.958,,µs/query").error
    )
