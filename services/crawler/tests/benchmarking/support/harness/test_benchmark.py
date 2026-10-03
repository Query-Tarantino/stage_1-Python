from services.crawler.tests.benchmarking.support.harness.benchmark import (
    Benchmark,
    iterations_of,
    sampled_operation,
    timed_operation,
    whole_run,
)
from services.crawler.tests.benchmarking.support.harness.iterations import (
    MICROSECONDS,
    SampledOperations,
    TimedOperations,
    WholeRuns,
)
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow


class Measured(Benchmark):
    STRUCTURES = ("json", "folders")

    @whole_run(warm_up=0)
    def build(self) -> None:
        pass

    def helper(self) -> None:
        pass

    @timed_operation(MICROSECONDS)
    def lookup(self) -> None:
        pass

    @sampled_operation(MICROSECONDS)
    def query(self) -> None:
        pass


def test_lists_its_measured_methods_in_the_order_they_are_declared():
    assert Measured.measured_methods() == ["build", "lookup", "query"]


def test_marks_each_method_with_how_it_is_measured():
    benchmark = Measured("json", 100)

    assert iterations_of(benchmark.build) == WholeRuns(warm_up=0, measured=3)
    assert iterations_of(benchmark.lookup) == TimedOperations(MICROSECONDS)
    assert iterations_of(benchmark.query) == SampledOperations(MICROSECONDS)


def test_keeps_the_rows_it_records_apart_by_kind():
    benchmark = Measured("json", 100)
    exact = ResultRow.exact("json", "term_count", 100, 106_410, "terms")
    sample = ResultRow.sample("json", "build_memory", 100, 41e6, "bytes")

    benchmark.record_exact([exact])
    benchmark.record_sample(sample)

    assert benchmark.exact_rows == [exact]
    assert benchmark.sample_rows == [sample]
