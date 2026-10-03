import os
import sys
from pathlib import Path

import pytest

from services.crawler.tests.benchmarking.support.environment.benchmark_options import (
    BenchmarkOptions,
)
from services.crawler.tests.benchmarking.support.harness.benchmark import (
    Benchmark,
    timed_operation,
    whole_run,
)
from services.crawler.tests.benchmarking.support.processes.benchmark_passes import (
    BenchmarkPasses,
)
from services.crawler.tests.benchmarking.support.results.metric import Metric
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow

# Measured processes import the benchmarks from the project root, as a run does
PROJECT_ROOT = Path(__file__).parents[6]


class Probe(Benchmark):
    STRUCTURES = ("json", "mongo")
    SIZES = (100, 300)

    @whole_run(warm_up=0, measured=1)
    def build(self) -> None:
        pass

    @timed_operation()
    def lookup(self) -> None:
        pass

    def teardown_trial(self) -> None:
        self.record_exact(
            [ResultRow.exact(self.structure, "process", self.books, os.getpid(), "pid")]
        )


class Failing(Benchmark):
    STRUCTURES = ("json",)
    SIZES = (1,)

    def setup_trial(self) -> None:
        raise RuntimeError("the cache is empty")

    @whole_run()
    def build(self) -> None:
        pass


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    # The processes import what this one does, also when the services are not
    # installed and only pytest's pythonpath finds them
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(sys.path))
    monkeypatch.setenv("TARANTINO_BENCHMARKS", str(tmp_path))
    monkeypatch.chdir(PROJECT_ROOT)


def test_reverses_the_structures_and_sizes_of_every_benchmark_in_the_second_pass():
    passes = BenchmarkPasses("probe", [Probe], BenchmarkOptions())

    first = [(c.method, c.structure, c.books) for c in passes.configurations(1)]
    second = [(c.method, c.structure, c.books) for c in passes.configurations(2)]

    assert first == [
        ("build", "json", 100), ("build", "json", 300),
        ("build", "mongo", 100), ("build", "mongo", 300),
        ("lookup", "json", 100), ("lookup", "json", 300),
        ("lookup", "mongo", 100), ("lookup", "mongo", 300),
    ]  # fmt: skip
    assert second == [
        ("build", "mongo", 300), ("build", "mongo", 100),
        ("build", "json", 300), ("build", "json", 100),
        ("lookup", "mongo", 300), ("lookup", "mongo", 100),
        ("lookup", "json", 300), ("lookup", "json", 100),
    ]  # fmt: skip


def test_measures_each_configuration_in_a_process_of_its_own(scratch):
    options = BenchmarkOptions(books=(100,), quick=True, skip_mongo=True)

    results = BenchmarkPasses("probe", [Probe], options).run()

    rows = results.rows(
        {
            "build": Metric.as_measured("build", "ms"),
            "lookup": Metric.as_measured("lookup", "ms"),
        }
    )
    assert [(row.metric, row.structure, row.books) for row in rows] == [
        ("build", "json", 100), ("lookup", "json", 100), ("process", "json", 100)
    ]  # fmt: skip
    assert rows[2].value != os.getpid()


def test_stops_the_run_when_a_process_fails(scratch):
    passes = BenchmarkPasses("probe", [Failing], BenchmarkOptions(quick=True))

    with pytest.raises(RuntimeError, match="Failing.build json 1 failed"):
        passes.run()
