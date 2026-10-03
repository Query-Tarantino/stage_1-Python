from __future__ import annotations

import gc
import tracemalloc
from typing import Callable, Tuple, TypeVar

T = TypeVar("T")


class Heap:
    @staticmethod
    def retained_by(build: Callable[[], T]) -> Tuple[int, T]:
        tracemalloc.start()
        try:
            gc.collect()
            before = tracemalloc.get_traced_memory()[0]
            built = build()
            gc.collect()
            return tracemalloc.get_traced_memory()[0] - before, built
        finally:
            tracemalloc.stop()
