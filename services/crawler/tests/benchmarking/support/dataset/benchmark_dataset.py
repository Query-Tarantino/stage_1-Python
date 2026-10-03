from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from tarantino_crawler.model.whitespace import JAVA_WHITESPACE

from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)


class BenchmarkDataset:
    # The books of the cache, in cache order: the dataset of size N is the first N,
    # and the new books are positions 1001 to 1100 (SPEC §11). It is also the
    # downloader of the benchmarks, which never touch the network.
    NEW_BOOKS = 100
    NEW_BOOKS_OFFSET = 1000

    def __init__(self, cache: Path, book_ids: Path):
        self._cache = cache
        self._book_ids = book_ids
        self._cached_ids: Optional[List[int]] = None

    @staticmethod
    def from_environment() -> BenchmarkDataset:
        return BenchmarkDataset(
            BenchmarkPaths.benchmarks() / "cache",
            BenchmarkPaths.workload() / "book_ids.txt",
        )

    def ids(self, count: int, offset: int = 0) -> List[int]:
        ids = self._ids_in_cache()
        if offset + count > len(ids):
            raise RuntimeError(
                f"The cache holds {len(ids)} books but {offset + count} are needed;"
                " run scripts/fill_cache.sh"
            )
        return ids[offset : offset + count]

    def new_ids(self) -> List[int]:
        return self.ids(self.NEW_BOOKS, self.NEW_BOOKS_OFFSET)

    def raw_text(self, book_id: int) -> str:
        return self._cache_file(book_id).read_text(encoding="utf-8")

    def _ids_in_cache(self) -> List[int]:
        if self._cached_ids is None:
            self._cached_ids = [
                book_id
                for book_id in self._candidate_ids()
                if self._cache_file(book_id).exists()
            ]
        return self._cached_ids

    def _candidate_ids(self) -> List[int]:
        lines = self._book_ids.read_text(encoding="utf-8").split("\n")
        stripped = (line.strip(JAVA_WHITESPACE) for line in lines)
        return [int(line) for line in stripped if line]

    def _cache_file(self, book_id: int) -> Path:
        return self._cache / f"{book_id}.txt"
