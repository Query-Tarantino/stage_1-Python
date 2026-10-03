from __future__ import annotations

from typing import Dict, Iterator, List, Mapping, Tuple

from services.crawler.tests.benchmarking.support.harness.iterations import SCORE
from services.crawler.tests.benchmarking.support.processes.configuration import (
    Configuration,
)
from services.crawler.tests.benchmarking.support.processes.process_result import (
    ProcessResult,
)
from services.crawler.tests.benchmarking.support.results.metric import Metric
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow
from services.crawler.tests.benchmarking.support.results.sample_statistics import (
    SampleStatistics,
)

Measure = Tuple[str, str, int]


class RunResults:
    # What the processes of a run measured. Each configuration gets the samples of its
    # processes in every pass, as a single run forking that many processes would
    # (SPEC §11); of the rows the benchmarks recorded, exact measures keep the first
    # process's and samples give their mean.

    def __init__(self):
        self._samples: Dict[Configuration, Dict[str, List[float]]] = {}
        self._exact_rows: Dict[Measure, ResultRow] = {}
        self._sample_rows: Dict[Measure, List[ResultRow]] = {}

    def add(self, configuration: Configuration, result: ProcessResult) -> None:
        series = self._samples.setdefault(configuration, {})
        for name, samples in result.samples.items():
            series.setdefault(name, []).extend(samples)
        for row in result.exact_rows:
            self._exact_rows.setdefault(self._measure(row), row)
        for row in result.sample_rows:
            self._sample_rows.setdefault(self._measure(row), []).append(row)

    def rows(self, metrics: Mapping[str, Metric]) -> List[ResultRow]:
        # The metric of each measured method: its score is the metric, and any other
        # series of its samples, such as p99, is <metric>_<series>
        return [
            *self._timed_rows(metrics),
            *self._exact_rows.values(),
            *(self._mean(samples) for samples in self._sample_rows.values()),
        ]

    def _timed_rows(self, metrics: Mapping[str, Metric]) -> Iterator[ResultRow]:
        for configuration, series in self._samples.items():
            for name, samples in series.items():
                metric = metrics[configuration.method]
                named = (
                    metric if name == SCORE else metric.named(f"{metric.name}_{name}")
                )
                yield named.row(
                    configuration.structure,
                    configuration.books,
                    SampleStatistics.mean(samples),
                    SampleStatistics.mean_error(samples, ResultRow.CONFIDENCE),
                )

    @staticmethod
    def _mean(samples: List[ResultRow]) -> ResultRow:
        values = [sample.value for sample in samples]
        first = samples[0]
        return ResultRow(
            first.structure,
            first.metric,
            first.books,
            SampleStatistics.mean(values),
            SampleStatistics.mean_error(values, ResultRow.CONFIDENCE),
            first.unit,
        )

    @staticmethod
    def _measure(row: ResultRow) -> Measure:
        return row.structure, row.metric, row.books
