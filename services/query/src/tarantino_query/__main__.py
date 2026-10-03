import io
import sys
from typing import Optional

from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.model.search_result import SearchResult
from tarantino_query.query_config import QueryConfig
from tarantino_query.query_factory import QueryFactory


def line(book: BookMetadata) -> str:
    return (
        f"  [{book.book_id}] {field(book.title)} — {field(book.author)}"
        f" ({field(book.language)}) {book.path}"
    )


def field(value: Optional[str]) -> str:
    # A missing field is written null, as Java prints it (SPEC §15)
    return "null" if value is None else value


def print_result(result: SearchResult) -> None:
    print(f'{len(result.books)} result(s) for "{result.query}"')
    for book in result.books:
        print(line(book))


def main() -> None:
    # UTF-8 lines on every operating system (SPEC §15)
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    # A wrong configuration stops the service before any work (SPEC §15)
    try:
        search = QueryFactory.search_command(QueryConfig.from_environment())
    except (OSError, ValueError) as error:
        sys.exit(f"tarantino_query: {error}")
    print_result(search.execute(" ".join(args)))


if __name__ == "__main__":
    main()
