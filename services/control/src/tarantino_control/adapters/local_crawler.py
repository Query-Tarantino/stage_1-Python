from __future__ import annotations

from tarantino_control.model.outcome import Outcome
from tarantino_control.ports.crawler import Crawler
from tarantino_crawler.commands.ingest_book_command import IngestBookCommand
from tarantino_crawler.commands.ingest_result import IngestResult


class LocalCrawler(Crawler):
    def __init__(self, ingest_command: IngestBookCommand):
        self.ingest_command = ingest_command

    def ingest(self, book_id: int) -> Outcome:
        return self._outcome(self.ingest_command.execute(book_id))

    @staticmethod
    def _outcome(result: IngestResult) -> Outcome:
        if result.succeeded():
            return Outcome.success(f"stored in {result.paths.body.parent}")
        else:
            return Outcome.failure(f"skipped, {result.failure.name}")
