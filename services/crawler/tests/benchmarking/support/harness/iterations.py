from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

NANOSECONDS_PER_SECOND = 1_000_000_000
MILLISECONDS = 1_000_000
MICROSECONDS = 1_000
SCORE = "score"
P99 = "p99"
BATCH_NANOSECONDS = 1_000_000

Operation = Callable[[], Any]


@dataclass(frozen=True)
class IterationOptions:
    warm_up: Optional[int] = None
    measured: Optional[int] = None
    seconds: float = 1.0

    def kinds(self, warm_up: int, measured: int) -> List[bool]:
        warm_up = warm_up if self.warm_up is None else self.warm_up
        measured = measured if self.measured is None else self.measured
        return [False] * warm_up + [True] * measured

    def nanoseconds(self) -> int:
        return round(self.seconds * NANOSECONDS_PER_SECOND)


class IterationHooks(Protocol):
    def setup_iteration(self, measured: bool) -> None: ...

    def teardown_iteration(self, measured: bool) -> None: ...


class Iterations(Protocol):
    def samples(
        self, hooks: IterationHooks, operation: Operation, options: IterationOptions
    ) -> Dict[str, List[float]]: ...


@dataclass(frozen=True)
class WholeRuns:
    warm_up: int
    measured: int

    def samples(
        self, hooks: IterationHooks, operation: Operation, options: IterationOptions
    ) -> Dict[str, List[float]]:
        samples = []
        for measured in options.kinds(self.warm_up, self.measured):
            hooks.setup_iteration(measured)
            start = time.perf_counter_ns()
            operation()
            elapsed = time.perf_counter_ns() - start
            hooks.teardown_iteration(measured)
            if measured:
                samples.append(elapsed / MILLISECONDS)
        return {SCORE: samples}


@dataclass(frozen=True)
class TimedOperations:
    unit: int
    warm_up: int = 3
    measured: int = 5

    def samples(
        self, hooks: IterationHooks, operation: Operation, options: IterationOptions
    ) -> Dict[str, List[float]]:
        samples = []
        for measured in options.kinds(self.warm_up, self.measured):
            hooks.setup_iteration(measured)
            operations, elapsed = self._repeat(operation, options.nanoseconds())
            hooks.teardown_iteration(measured)
            if measured:
                samples.append(elapsed / operations / self.unit)
        return {SCORE: samples}

    @staticmethod
    def _repeat(operation: Operation, nanoseconds: int) -> Tuple[int, int]:
        operations, batch = 0, 1
        start = now = time.perf_counter_ns()
        while now - start < nanoseconds:
            for _ in range(batch):
                operation()
            operations += batch
            previous, now = now, time.perf_counter_ns()
            if now - previous < BATCH_NANOSECONDS:
                batch *= 2
        return operations, now - start


@dataclass(frozen=True)
class SampledOperations:
    unit: int
    warm_up: int = 3
    measured: int = 5

    def samples(
        self, hooks: IterationHooks, operation: Operation, options: IterationOptions
    ) -> Dict[str, List[float]]:
        means, percentiles = [], []
        for measured in options.kinds(self.warm_up, self.measured):
            hooks.setup_iteration(measured)
            times = self._time_each(operation, options.nanoseconds())
            hooks.teardown_iteration(measured)
            if measured:
                means.append(statistics.fmean(times) / self.unit)
                percentiles.append(self.percentile(times, 99) / self.unit)
        return {SCORE: means, P99: percentiles}

    @staticmethod
    def percentile(times: List[int], rank: float) -> float:
        ordered = sorted(times)
        return ordered[max(math.ceil(len(ordered) * rank / 100), 1) - 1]

    @staticmethod
    def _time_each(operation: Operation, nanoseconds: int) -> List[int]:
        times = []
        start = now = time.perf_counter_ns()
        while now - start < nanoseconds:
            before = time.perf_counter_ns()
            operation()
            now = time.perf_counter_ns()
            times.append(now - before)
        return times
