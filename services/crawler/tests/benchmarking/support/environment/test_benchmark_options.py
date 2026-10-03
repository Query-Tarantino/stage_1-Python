from services.crawler.tests.benchmarking.support.environment.benchmark_options import (
    BenchmarkOptions,
)
from services.crawler.tests.benchmarking.support.harness.iterations import (
    IterationOptions,
)

LAYOUTS = ("time", "book", "batch")
SIZES = (100, 300, 1000)


def test_runs_a_second_pass_with_every_parameter_in_reverse_order():
    options = BenchmarkOptions.from_environment({})

    assert options.passes() == 2
    assert options.structures(LAYOUTS, 1) == ["time", "book", "batch"]
    assert options.structures(LAYOUTS, 2) == ["batch", "book", "time"]
    assert options.sizes(SIZES, 2) == [1000, 300, 100]


def test_reverses_overridden_sizes_without_repeating_them():
    options = BenchmarkOptions.from_environment(
        {"TARANTINO_BENCHMARK_BOOKS": "100,300"}
    )

    assert options.sizes(SIZES, 1) == [100, 300]
    assert options.sizes(SIZES, 2) == [300, 100]


def test_runs_one_short_pass_in_quick_mode():
    options = BenchmarkOptions.from_environment({"TARANTINO_BENCHMARK_QUICK": "true"})

    assert options.passes() == 1
    assert options.iterations() == IterationOptions(warm_up=1, measured=1, seconds=0.2)


def test_runs_the_iterations_each_benchmark_declares_in_a_full_run():
    assert BenchmarkOptions.from_environment({}).iterations() == IterationOptions()


def test_leaves_mongo_out_when_asked():
    options = BenchmarkOptions.from_environment(
        {"TARANTINO_BENCHMARK_SKIP_MONGO": "true"}
    )

    assert options.structures(("json", "folders", "mongo"), 1) == ["json", "folders"]
    assert options.structures(LAYOUTS, 1) == list(LAYOUTS)


def test_ignores_blank_and_false_variables():
    options = BenchmarkOptions.from_environment(
        {"TARANTINO_BENCHMARK_BOOKS": " ", "TARANTINO_BENCHMARK_QUICK": "false"}
    )

    assert options == BenchmarkOptions()
