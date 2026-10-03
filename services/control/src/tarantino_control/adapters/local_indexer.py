from __future__ import annotations

from tarantino_control.model.outcome import Outcome
from tarantino_control.ports.indexer import Indexer
from tarantino_indexer.commands.index_book_command import IndexBookCommand
from tarantino_indexer.commands.index_result import IndexResult


class LocalIndexer(Indexer):
    def __init__(self, index_command: IndexBookCommand):
        self.index_command = index_command

    def index(self, book_id: int) -> Outcome:
        return self._outcome(self.index_command.execute(book_id))

    @staticmethod
    def _outcome(result: IndexResult) -> Outcome:
        if result.indexed:
            return Outcome.success(f"{result.unique_terms} unique terms indexed")
        else:
            return Outcome.failure("skipped, not found in the datalake")
