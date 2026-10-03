import io
import sys

from tarantino_indexer.commands.index_result import IndexResult
from tarantino_indexer.indexer_config import IndexerConfig
from tarantino_indexer.indexer_factory import IndexerFactory


def main():
    # UTF-8 lines on every operating system (SPEC §15)
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    # A wrong argument or configuration stops the service before any work (SPEC §15)
    try:
        index = IndexerFactory.index_command(IndexerConfig.from_environment())
        book_ids = [book_id_of(arg) for arg in sys.argv[1:]]
    except (OSError, ValueError) as error:
        sys.exit(f"tarantino_indexer: {error}")

    for book_id in book_ids:
        print(line(index.execute(book_id)))


def book_id_of(argument: str) -> int:
    try:
        return int(argument)
    except ValueError:
        raise ValueError(f"not a book id: {argument}") from None


def line(result: IndexResult) -> str:
    # One line per book, in the words of the control service (SPEC §15)
    if result.indexed:
        return f"[INDEXER] {result.book_id}: {result.unique_terms} unique terms indexed"
    return f"[INDEXER] {result.book_id}: skipped, not found in the datalake"


if __name__ == "__main__":
    main()
