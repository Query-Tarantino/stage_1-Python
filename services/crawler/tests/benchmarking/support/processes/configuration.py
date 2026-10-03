from __future__ import annotations

import importlib
import json
from dataclasses import asdict, dataclass
from typing import Type

from services.crawler.tests.benchmarking.support.harness.benchmark import Benchmark


@dataclass(frozen=True)
class Configuration:
    benchmark: str
    method: str
    structure: str
    books: int

    @staticmethod
    def of(
        benchmark: Type[Benchmark], method: str, structure: str, books: int
    ) -> Configuration:
        name = f"{benchmark.__module__}:{benchmark.__qualname__}"
        return Configuration(name, method, structure, books)

    @staticmethod
    def from_json(text: str) -> Configuration:
        return Configuration(**json.loads(text))

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    def benchmark_class(self) -> Type[Benchmark]:
        module, name = self.benchmark.split(":")
        return getattr(importlib.import_module(module), name)

    def __str__(self) -> str:
        class_name = self.benchmark.split(":")[1]
        return f"{class_name}.{self.method} {self.structure} {self.books}"
