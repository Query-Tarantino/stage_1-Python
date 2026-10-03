from __future__ import annotations

import io
import sys

from tarantino_crawler.commands.ingest_result import IngestResult
from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_crawler.crawler_factory import CrawlerFactory


def main() -> None:
    # UTF-8 lines on every operating system (SPEC §15)
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    # A wrong argument or configuration stops the service before any work (SPEC §15)
    try:
        ingest = CrawlerFactory.ingest_command(CrawlerConfig.from_environment())
        book_ids = [book_id_of(arg) for arg in sys.argv[1:]]
    except (OSError, ValueError) as error:
        sys.exit(f"tarantino_crawler: {error}")

    for book_id in book_ids:
        print(line(ingest.execute(book_id)))


def book_id_of(argument: str) -> int:
    try:
        return int(argument)
    except ValueError:
        raise ValueError(f"not a book id: {argument}") from None


def line(result: IngestResult) -> str:
    # One line per book, in the words of the control service (SPEC §15)
    if result.succeeded():
        return f"[CRAWLER] {result.book_id}: stored in {result.paths.body.parent}"
    return f"[CRAWLER] {result.book_id}: skipped, {result.failure.name}"


if __name__ == "__main__":
    main()
