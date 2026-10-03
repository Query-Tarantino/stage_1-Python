from __future__ import annotations

import gc
import tracemalloc
from typing import Callable, Tuple, TypeVar

T = TypeVar("T")


class Heap:
    @staticmethod
    def retained_by(build: Callable[[], T]) -> Tuple[int, T]:
        # The memory that what build returns keeps, as traced by tracemalloc after a
        # collection, minus the same measure before it (SPEC §11). Tracing slows Python
        # down several times, so it runs only around this measure; it leaves out what
        # native libraries allocate on their own. What build returns is returned too,
        # so that it is still alive when the second measure is taken.
        tracemalloc.start()
        try:
            gc.collect()
            before = tracemalloc.get_traced_memory()[0]
            built = build()
            gc.collect()
            return tracemalloc.get_traced_memory()[0] - before, built
        finally:
            tracemalloc.stop()
