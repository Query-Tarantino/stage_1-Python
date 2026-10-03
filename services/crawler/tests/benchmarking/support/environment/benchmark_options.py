from __future__ import annotations

import os
from dataclasses import dataclass
from typing import ClassVar, List, Mapping, Optional, Sequence, Tuple, TypeVar

from tarantino_crawler.model.whitespace import JAVA_WHITESPACE

from services.crawler.tests.benchmarking.support.harness.iterations import (
    IterationOptions,
)

T = TypeVar("T")


@dataclass(frozen=True)
class BenchmarkOptions:
    # What the variables of a run set (Java's BenchmarkOptions): the sizes, a quick run
    # to check the setup, and leaving MongoDB out
    QUICK_ITERATIONS: ClassVar[IterationOptions] = IterationOptions(
        warm_up=1, measured=1, seconds=0.2
    )
    MONGO: ClassVar[str] = "mongo"

    books: Optional[Tuple[int, ...]] = None
    quick: bool = False
    skip_mongo: bool = False

    @staticmethod
    def from_environment(
        environment: Mapping[str, str] = os.environ,
    ) -> BenchmarkOptions:
        books = BenchmarkOptions._variable(environment, "TARANTINO_BENCHMARK_BOOKS")
        return BenchmarkOptions(
            books=tuple(int(size) for size in books.split(",")) if books else None,
            quick=BenchmarkOptions._enabled(environment, "TARANTINO_BENCHMARK_QUICK"),
            skip_mongo=BenchmarkOptions._enabled(
                environment, "TARANTINO_BENCHMARK_SKIP_MONGO"
            ),
        )

    def passes(self) -> int:
        # Two passes in a full run, the second with every structure and size in
        # reverse order, so that whatever drifts during a run, such as the
        # temperature or the writes left by the benchmark before, weighs alike on
        # every structure and size instead of always on the last ones (SPEC §11); one
        # in a quick run
        return 1 if self.quick else 2

    def iterations(self) -> IterationOptions:
        # A quick run takes 1 warm-up and 1 measured iteration of 0.2 s, to check the
        # setup: its numbers are not meaningful
        return self.QUICK_ITERATIONS if self.quick else IterationOptions()

    def structures(self, declared: Sequence[str], pass_number: int) -> List[str]:
        kept = [s for s in declared if not (self.skip_mongo and s == self.MONGO)]
        return self._in_pass_order(kept, pass_number)

    def sizes(self, declared: Sequence[int], pass_number: int) -> List[int]:
        return self._in_pass_order(
            list(self.books if self.books else declared), pass_number
        )

    @staticmethod
    def _in_pass_order(values: List[T], pass_number: int) -> List[T]:
        return values if pass_number == 1 else values[::-1]

    @staticmethod
    def _variable(environment: Mapping[str, str], name: str) -> Optional[str]:
        value = environment.get(name, "")
        return value if value.strip(JAVA_WHITESPACE) else None

    @staticmethod
    def _enabled(environment: Mapping[str, str], name: str) -> bool:
        value = BenchmarkOptions._variable(environment, name)
        return value is not None and value.lower() == "true"
