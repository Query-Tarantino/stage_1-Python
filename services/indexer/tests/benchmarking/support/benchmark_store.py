from __future__ import annotations

import json
from pathlib import Path
from typing import Collection

from tarantino_indexer.indexer_config import IndexerConfig
from tarantino_indexer.indexer_factory import IndexerFactory
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)
from tarantino_indexer.ports.datamarts.metadata_storage import MetadataStorage

from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)
from services.crawler.tests.benchmarking.support.files.directories import Directories
from services.indexer.tests.adapters.index.folders.term_file_restore import (
    TermFileRestore,
)
from services.indexer.tests.benchmarking.support.mongo_stores import MongoStores
from services.indexer.tests.benchmarking.support.store_footprint import (
    StoreFootprint,
)


class BenchmarkStore:
    # The datamarts of a benchmark: a directory of the scratch area and, for mongo, a
    # database of its own named after it
    MONGO = "mongo"
    FOLDERS = "folders"
    INVERTED_INDEX = "inverted_index"

    def __init__(self, config: IndexerConfig, mongo: bool):
        self._config = config
        self._mongo = mongo

    @staticmethod
    def for_index(index: str, name: str) -> BenchmarkStore:
        return BenchmarkStore(
            BenchmarkStore._config(name, index, "sqlite"), index == BenchmarkStore.MONGO
        )

    @staticmethod
    def for_metadata(metadata: str, name: str) -> BenchmarkStore:
        return BenchmarkStore(
            BenchmarkStore._config(name, "json", metadata),
            metadata == BenchmarkStore.MONGO,
        )

    @property
    def datamarts(self) -> Path:
        return self._config.datamarts

    @property
    def mongo_uri(self) -> str:
        return self._config.mongo_uri

    def inverted_index(self) -> InvertedIndexStorage:
        return IndexerFactory.inverted_index(self._config)

    def metadata(self) -> MetadataStorage:
        return IndexerFactory.metadata(self._config)

    def clear(self) -> None:
        Directories.delete(self._config.datamarts)
        if self._mongo:
            MongoStores.drop(self._config.mongo_uri)

    def copy_to(self, target: BenchmarkStore) -> None:
        target.clear()
        Directories.copy(self._config.datamarts, target.datamarts)
        if self._mongo:
            MongoStores.copy(self._config.mongo_uri, target.mongo_uri)

    def restore_terms_from(
        self, snapshot: BenchmarkStore, touched_terms: Collection[str]
    ) -> None:
        # Restores the snapshot after an update that only touched the given terms. For
        # folders and MongoDB only their files or documents are put back, instead of
        # hundreds of thousands of them; json, a single file, is copied.
        if self._config.index == self.FOLDERS:
            TermFileRestore.restore(
                snapshot._folder_index(), self._folder_index(), touched_terms
            )
        elif self._config.index == self.MONGO:
            MongoStores.restore_documents(
                snapshot.mongo_uri,
                self.mongo_uri,
                self.INVERTED_INDEX,
                "term",
                touched_terms,
            )
        else:
            snapshot.copy_to(self)

    def footprint(self) -> StoreFootprint:
        # Measures the index once it is flushed. MongoDB reports allocated storage, so
        # its two sizes are equal; a folders index is walked once for its files, sizes
        # and blocks.
        if self._mongo:
            stored = MongoStores.disk_usage(self.mongo_uri)
            terms = MongoStores.document_count(self.mongo_uri, self.INVERTED_INDEX)
            return StoreFootprint(stored, stored, terms)
        if self._config.index == self.FOLDERS:
            folders = Directories.footprint(self._folder_index())
            return StoreFootprint(folders.bytes, folders.allocated_bytes, folders.files)
        files = Directories.footprint(self.datamarts)
        index = json.loads(
            (self.datamarts / "inverted_index.json").read_text(encoding="utf-8")
        )
        return StoreFootprint(files.bytes, files.allocated_bytes, len(index))

    def _folder_index(self) -> Path:
        return self.datamarts / self.INVERTED_INDEX

    @staticmethod
    def _config(name: str, index: str, metadata: str) -> IndexerConfig:
        return IndexerConfig(
            datalake=Path("datalake"),
            datalake_layout="time",
            datamarts=BenchmarkPaths.scratch(name),
            index=index,
            metadata=metadata,
            mongo_uri=BenchmarkPaths.mongo_uri(name.replace("-", "_")),
            workload=BenchmarkPaths.workload(),
        )
