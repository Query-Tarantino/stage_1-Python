from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import List

from services.crawler.tests.benchmarking.support.harness.benchmark import iterations_of
from services.crawler.tests.benchmarking.support.harness.iterations import (
    IterationOptions,
)
from services.crawler.tests.benchmarking.support.processes.configuration import (
    Configuration,
)
from services.crawler.tests.benchmarking.support.processes.process_result import (
    ProcessResult,
)


class MeasuredProcess:
    # The process that measures one configuration, as a JMH fork (SPEC §11): it runs
    # the hooks of the trial around the iterations of the measured method and writes
    # what it measured to a file, so that the run reads it whatever the benchmark
    # prints.

    @staticmethod
    def command(
        configuration: Configuration, options: IterationOptions, result: Path
    ) -> List[str]:
        options_json = json.dumps(asdict(options))
        return [
            sys.executable,
            "-m",
            __name__,
            configuration.to_json(),
            options_json,
            str(result),
        ]

    @staticmethod
    def measure(
        configuration: Configuration, options: IterationOptions
    ) -> ProcessResult:
        benchmark_class = configuration.benchmark_class()
        benchmark = benchmark_class(configuration.structure, configuration.books)
        method = getattr(benchmark, configuration.method)
        benchmark.setup_trial()
        samples = iterations_of(method).samples(benchmark, method, options)
        benchmark.teardown_trial()
        return ProcessResult(samples, benchmark.exact_rows, benchmark.sample_rows)


def main(arguments: List[str]) -> None:
    configuration = Configuration.from_json(arguments[0])
    options = IterationOptions(**json.loads(arguments[1]))
    result = MeasuredProcess.measure(configuration, options)
    Path(arguments[2]).write_text(result.to_json(), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
