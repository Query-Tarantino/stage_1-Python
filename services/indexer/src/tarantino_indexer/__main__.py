import io
import sys

from tarantino_indexer.commands.index_result import IndexResult
from tarantino_indexer.indexer_config import IndexerConfig
from tarantino_indexer.indexer_factory import IndexerFactory


def main():
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        book_ids = [book_id_of(arg) for arg in sys.argv[1:]]
        index = IndexerFactory.index_command(IndexerConfig.from_environment())
    except (OSError, ValueError) as error:
        sys.exit(f"tarantino_indexer: {error}")

    for result in index.execute(book_ids):
        print(line(result))


def book_id_of(argument: str) -> int:
    try:
        return int(argument)
    except ValueError:
        raise ValueError(f"not a book id: {argument}") from None


def line(result: IndexResult) -> str:
    if result.indexed:
        return f"[INDEXER] {result.book_id}: {result.unique_terms} unique terms indexed"
    return f"[INDEXER] {result.book_id}: skipped, not found in the datalake"


if __name__ == "__main__":
    main()
