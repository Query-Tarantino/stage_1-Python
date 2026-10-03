from __future__ import annotations

import subprocess
import time
from typing import List, Sequence, Type

from services.crawler.tests.benchmarking.support.environment.benchmark_options import (
    BenchmarkOptions,
)
from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)
from services.crawler.tests.benchmarking.support.harness.benchmark import Benchmark
from services.crawler.tests.benchmarking.support.processes.configuration import (
    Configuration,
)
from services.crawler.tests.benchmarking.support.processes.measured_process import (
    MeasuredProcess,
)
from services.crawler.tests.benchmarking.support.processes.process_result import (
    ProcessResult,
)
from services.crawler.tests.benchmarking.support.results.run_results import (
    RunResults,
)


class BenchmarkPasses:

    def __init__(
        self,
        service: str,
        benchmarks: Sequence[Type[Benchmark]],
        options: BenchmarkOptions,
    ):
        self._service = service
        self._benchmarks = benchmarks
        self._options = options

    def run(self) -> RunResults:
        results = RunResults()
        passes = self._options.passes()
        for pass_number in range(1, passes + 1):
            configurations = self.configurations(pass_number)
            for position, configuration in enumerate(configurations, 1):
                print(
                    f"Pass {pass_number}/{passes}, {position}/{len(configurations)}:"
                    f" {configuration}",
                    end="",
                    flush=True,
                )
                start = time.monotonic()
                results.add(configuration, self._measure(configuration))
                print(f" ({time.monotonic() - start:.0f} s)", flush=True)
        return results

    def configurations(self, pass_number: int) -> List[Configuration]:
        return [
            Configuration.of(benchmark, method, structure, books)
            for benchmark in self._benchmarks
            for method in benchmark.measured_methods()
            for structure in self._options.structures(benchmark.STRUCTURES, pass_number)
            for books in self._options.sizes(benchmark.SIZES, pass_number)
        ]

    def _measure(self, configuration: Configuration) -> ProcessResult:
        result = BenchmarkPaths.scratch(f"process-result-{self._service}.json")
        result.parent.mkdir(parents=True, exist_ok=True)
        result.unlink(missing_ok=True)
        command = MeasuredProcess.command(
            configuration, self._options.iterations(), result
        )
        exit_status = subprocess.run(command).returncode
        if exit_status != 0:
            raise RuntimeError(
                f"{configuration} failed with exit status {exit_status};"
                " no results were written"
            )
        measured = ProcessResult.from_json(result.read_text(encoding="utf-8"))
        result.unlink()
        return measured
