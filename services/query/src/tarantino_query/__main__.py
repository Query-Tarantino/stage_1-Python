import sys

from tarantino_query.model.book_metadata import BookMetadata
from tarantino_query.model.search_result import SearchResult
from tarantino_query.query_config import QueryConfig
from tarantino_query.query_factory import QueryFactory


def line(book: BookMetadata) -> str:
    return (
        f"  [{book.book_id}] {book.title} — {book.author} ({book.language}) {book.path}"
    )


def print_result(result: SearchResult) -> None:
    print(f'{len(result.books)} result(s) for "{result.query}"')
    for book in result.books:
        print(line(book))


def main() -> None:
    args = sys.argv[1:]
    search = QueryFactory.search_command(QueryConfig.from_environment())
    print_result(search.execute(" ".join(args)))


if __name__ == "__main__":
    main()
