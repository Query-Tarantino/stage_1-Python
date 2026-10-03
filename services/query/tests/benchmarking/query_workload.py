from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence, Set

from tarantino_query.adapters.stopwords.file_stopwords_loader import (
    FileStopwordsLoader,
)
from tarantino_query.commands.search_command import SearchCommand
from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.model.whitespace import JAVA_WHITESPACE
from tarantino_query.ports.metadata_reader import MetadataReader
from tarantino_query.query_config import QueryConfig
from tarantino_query.query_factory import QueryFactory

from services.crawler.tests.benchmarking.support.environment.benchmark_paths import (
    BenchmarkPaths,
)
from services.indexer.tests.benchmarking.support.benchmark_store import BenchmarkStore
from services.query.tests.benchmarking.workload_query import WorkloadQuery


class ConstantMetadata(MetadataReader):
    BODY = Path("body.txt")

    def book(self, book_id: int) -> Optional[BookMetadata]:
        return BookMetadata(book_id, "title", "author", "English", self.BODY)

    def books_by(self, author: str) -> List[BookMetadata]:
        return []


class QueryWorkload:
    ALL_CATEGORIES = "all"
    CONSTANT_METADATA = ConstantMetadata()

    @staticmethod
    def open_search(
        store: BenchmarkStore, index: str, stopwords: Set[str]
    ) -> SearchCommand:
        config = QueryConfig(
            store.datamarts, index, "sqlite", store.mongo_uri, BenchmarkPaths.workload()
        )
        return SearchCommand(
            QueryFactory.inverted_index(config),
            QueryWorkload.CONSTANT_METADATA,
            stopwords,
        )

    @staticmethod
    def stopwords() -> Set[str]:
        return FileStopwordsLoader(
            BenchmarkPaths.workload() / "stopwords.txt"
        ).stopwords()

    @staticmethod
    def queries() -> List[WorkloadQuery]:
        file = BenchmarkPaths.workload() / "queries.txt"
        lines = file.read_text(encoding="utf-8").split("\n")
        return [
            WorkloadQuery.parse(line) for line in lines if line.strip(JAVA_WHITESPACE)
        ]

    @staticmethod
    def texts(queries: Sequence[WorkloadQuery], category: str) -> List[str]:
        return [
            query.text
            for query in queries
            if category in (QueryWorkload.ALL_CATEGORIES, query.category)
        ]
