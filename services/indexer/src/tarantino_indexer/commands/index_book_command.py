from __future__ import annotations

from typing import List

from tarantino_indexer.commands.index_result import IndexResult
from tarantino_indexer.model.book.header_parser import HeaderParser
from tarantino_indexer.model.terms.tokenizer import Tokenizer
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)
from tarantino_indexer.ports.datamarts.metadata_storage import MetadataStorage
from tarantino_indexer.ports.sources.datalake_reader import DatalakeReader


class IndexBookCommand:
    def __init__(
        self,
        datalake: DatalakeReader,
        header_parser: HeaderParser,
        tokenizer: Tokenizer,
        inverted_index: InvertedIndexStorage,
        metadata: MetadataStorage,
    ):
        self.datalake = datalake
        self.header_parser = header_parser
        self.tokenizer = tokenizer
        self.inverted_index = inverted_index
        self.metadata = metadata

    def execute(self, book_ids: List[int]) -> List[IndexResult]:
        results = [self._add(book_id) for book_id in book_ids]
        if any(result.indexed for result in results):
            self.inverted_index.flush()
        return results

    def _add(self, book_id: int) -> IndexResult:
        text = self.datalake.book_text(book_id)
        if text is None:
            return IndexResult.not_found(book_id)
        self.metadata.save(self.header_parser.book(text))
        occurrences = self.tokenizer.occurrences(text.book_id, text.body)
        self.inverted_index.add(occurrences)
        return IndexResult.success(text.book_id, len(occurrences.frequencies))
