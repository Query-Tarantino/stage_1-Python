from __future__ import annotations

import random
import time
from typing import Dict, List

from tarantino_query.commands.search_command import SearchCommand
from tarantino_query.model.query_terms import QueryTerms
from tarantino_query.model.search_result import SearchResult

from services.crawler.tests.benchmarking.support.environment.heap import Heap
from services.crawler.tests.benchmarking.support.harness.benchmark import (
    Benchmark,
    sampled_operation,
)
from services.crawler.tests.benchmarking.support.harness.iterations import (
    MICROSECONDS,
)
from services.crawler.tests.benchmarking.support.results.result_row import ResultRow
from services.crawler.tests.benchmarking.support.validation.check import Check
from services.indexer.tests.benchmarking.support.index_fixture import IndexFixture
from services.indexer.tests.benchmarking.support.prebuilt_indexes import (
    PrebuiltIndexes,
)
from services.query.tests.benchmarking.query_workload import QueryWorkload
from services.query.tests.benchmarking.reference_results import ReferenceResults


class QueryTimeBenchmark(Benchmark):
    STRUCTURES = ("json", "folders", "mongo")
    QUERY_TIME_UNIT = "µs/query"
    INDEX_MEMORY_SAMPLES = 5

    def setup_trial(self) -> None:
        fixture = IndexFixture.from_environment()
        self._store = PrebuiltIndexes.of(self.structure, self.books, fixture)
        self._stopwords = QueryWorkload.stopwords()
        workload = QueryWorkload.queries()
        self._queries = QueryWorkload.texts(workload, QueryWorkload.ALL_CATEGORIES)
        self._categories = list(dict.fromkeys(query.category for query in workload))
        self._category_of_query = [
            self._categories.index(query.category) for query in workload
        ]
        self._search = self._open_and_answer_every_query()
        for _ in range(self.INDEX_MEMORY_SAMPLES):
            self._record_index_memory()
        self._require_reference_results(fixture)

    def setup_iteration(self, measured: bool) -> None:
        self._nanoseconds = [0] * len(self._categories)
        self._answered = [0] * len(self._categories)

    @sampled_operation(MICROSECONDS)
    def query_time(self) -> SearchResult:
        query = random.randrange(len(self._queries))
        category = self._category_of_query[query]
        start = time.perf_counter_ns()
        result = self._search.execute(self._queries[query])
        self._nanoseconds[category] += time.perf_counter_ns() - start
        self._answered[category] += 1
        return result

    def teardown_iteration(self, measured: bool) -> None:
        if not measured:
            return
        for category, name in enumerate(self._categories):
            if self._answered[category] > 0:
                microseconds = (
                    self._nanoseconds[category] / 1000 / self._answered[category]
                )
                self.record_sample(
                    ResultRow.sample(
                        self.structure,
                        f"query_time_{name}",
                        self.books,
                        microseconds,
                        self.QUERY_TIME_UNIT,
                    )
                )

    def _record_index_memory(self) -> None:
        self._search = None
        retained, self._search = Heap.retained_by(self._open_and_answer_every_query)
        self.record_sample(
            ResultRow.sample(
                self.structure, "index_memory", self.books, retained, "bytes"
            )
        )

    def _open_and_answer_every_query(self) -> SearchCommand:
        opened = QueryWorkload.open_search(self._store, self.structure, self._stopwords)
        for query in self._queries:
            opened.execute(query)
        return opened

    def _require_reference_results(self, fixture: IndexFixture) -> None:
        expected = self._reference_results(fixture)
        for query in self._queries:
            found = [book.book_id for book in self._search.execute(query).books]
            Check.require(found == expected[query], f"wrong result for query '{query}'")

    def _reference_results(self, fixture: IndexFixture) -> Dict[str, List[int]]:
        cached = PrebuiltIndexes.file(f"reference-results-{self.books}.tsv")
        if cached.exists():
            return ReferenceResults.read(cached)
        expected = self._computed_reference_results(fixture)
        ReferenceResults.write(cached, expected)
        return expected

    def _computed_reference_results(
        self, fixture: IndexFixture
    ) -> Dict[str, List[int]]:
        terms_of_query = {
            query: set(QueryTerms.of(query, self._stopwords)) for query in self._queries
        }
        expected: Dict[str, List[int]] = {query: [] for query in self._queries}
        for book_id in sorted(fixture.dataset.ids(self.books)):
            book_terms = fixture.terms(book_id)
            for query, terms in terms_of_query.items():
                if terms and terms <= book_terms:
                    expected[query].append(book_id)
        return expected
