from __future__ import annotations

from pathlib import Path
from typing import List

from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)
from services.crawler.tests.benchmarking.support.files.directories import Directories
from services.indexer.tests.benchmarking.support.benchmark_store import BenchmarkStore
from services.indexer.tests.benchmarking.support.index_fixture import IndexFixture


class PrebuiltIndexes:
    # Indexes of the first N books, built once per benchmark run and shared by every
    # process of the benchmarks that only need them as a starting point. Their content
    # is deterministic, so reusing them changes no result. A marker file says that one
    # is complete.
    PREFIX = "prebuilt-"
    BUILT_MARKER = ".built"
    WORKING_MARKER = ".working"

    @staticmethod
    def of(index: str, books: int, fixture: IndexFixture) -> BenchmarkStore:
        store = PrebuiltIndexes._built_store(index, books)
        marker = PrebuiltIndexes._marker(index, books, PrebuiltIndexes.BUILT_MARKER)
        if not marker.exists():
            store.clear()
            fixture.index(store.inverted_index(), fixture.dataset.ids(books))
            PrebuiltIndexes._create(marker)
        return store

    @staticmethod
    def working_copy_of(
        prebuilt: BenchmarkStore, index: str, books: int
    ) -> BenchmarkStore:
        # A copy for the benchmarks that update it, made once per run and shared by
        # every process and method, which put it back to the prebuilt index before each
        # run (SPEC §11) instead of copying it whole: for folders that is hundreds of
        # thousands of files
        store = PrebuiltIndexes._working_store(index, books)
        marker = PrebuiltIndexes._marker(index, books, PrebuiltIndexes.WORKING_MARKER)
        if not marker.exists():
            prebuilt.copy_to(store)
            PrebuiltIndexes._create(marker)
        return store

    @staticmethod
    def file(name: str) -> Path:
        return BenchmarkPaths.scratch(PrebuiltIndexes.PREFIX + name)

    @staticmethod
    def delete_all() -> None:
        for entry in PrebuiltIndexes._entries():
            PrebuiltIndexes._delete_store_of(entry)
        for entry in PrebuiltIndexes._entries():
            Directories.delete(entry)

    @staticmethod
    def _built_store(index: str, books: int) -> BenchmarkStore:
        return BenchmarkStore.for_index(
            index, f"{PrebuiltIndexes.PREFIX}index-{index}-{books}"
        )

    @staticmethod
    def _working_store(index: str, books: int) -> BenchmarkStore:
        return BenchmarkStore.for_index(
            index, f"{PrebuiltIndexes.PREFIX}working-{index}-{books}"
        )

    @staticmethod
    def _marker(index: str, books: int, kind: str) -> Path:
        return PrebuiltIndexes.file(f"{index}-{books}{kind}")

    @staticmethod
    def _delete_store_of(entry: Path) -> None:
        # A marker names the store it completes: prebuilt-<index>-<books>.<kind>
        name = entry.name
        for kind in (PrebuiltIndexes.BUILT_MARKER, PrebuiltIndexes.WORKING_MARKER):
            if name.endswith(kind):
                index, books = name[len(PrebuiltIndexes.PREFIX) : -len(kind)].split("-")
                if kind == PrebuiltIndexes.BUILT_MARKER:
                    PrebuiltIndexes._built_store(index, int(books)).clear()
                else:
                    PrebuiltIndexes._working_store(index, int(books)).clear()

    @staticmethod
    def _entries() -> List[Path]:
        root = BenchmarkPaths.scratch_root()
        if not root.is_dir():
            return []
        return [
            entry
            for entry in root.iterdir()
            if entry.name.startswith(PrebuiltIndexes.PREFIX)
        ]

    @staticmethod
    def _create(marker: Path) -> None:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch(exist_ok=False)
