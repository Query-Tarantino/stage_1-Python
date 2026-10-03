from __future__ import annotations

from typing import Dict, List

from tarantino_control.model.outcome import Outcome
from tarantino_control.ports.indexer import Indexer
from tarantino_indexer.commands.index_book_command import IndexBookCommand
from tarantino_indexer.commands.index_result import IndexResult


class LocalIndexer(Indexer):
    def __init__(self, index_command: IndexBookCommand):
        self.index_command = index_command

    def index(self, book_ids: List[int]) -> Dict[int, Outcome]:
        return {
            result.book_id: self._outcome(result)
            for result in self.index_command.execute(book_ids)
        }

    @staticmethod
    def _outcome(result: IndexResult) -> Outcome:
        if result.indexed:
            return Outcome.success(f"{result.unique_terms} unique terms indexed")
        else:
            return Outcome.failure("skipped, not found in the datalake")
