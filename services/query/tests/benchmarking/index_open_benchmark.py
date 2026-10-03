from __future__ import annotations

from tarantino_query.model.search_result import SearchResult

from services.crawler.tests.benchmarking.support.harness.benchmark import (
    Benchmark,
    whole_run,
)
from services.indexer.tests.benchmarking.support.index_fixture import IndexFixture
from services.indexer.tests.benchmarking.support.prebuilt_indexes import (
    PrebuiltIndexes,
)
from services.query.tests.benchmarking.query_workload import QueryWorkload


class IndexOpenBenchmark(Benchmark):
    STRUCTURES = ("json", "folders", "mongo")

    def setup_trial(self) -> None:
        self._store = PrebuiltIndexes.of(
            self.structure, self.books, IndexFixture.from_environment()
        )
        self._stopwords = QueryWorkload.stopwords()
        self._first_query = QueryWorkload.queries()[0].text

    @whole_run()
    def index_open_time(self) -> SearchResult:
        search = QueryWorkload.open_search(self._store, self.structure, self._stopwords)
        return search.execute(self._first_query)
