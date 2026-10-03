from __future__ import annotations

import sys

from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_crawler.crawler_factory import CrawlerFactory


def main() -> None:
    config = CrawlerConfig.from_environment()
    ingest = CrawlerFactory.ingest_command(config)

    book_ids = [int(arg) for arg in sys.argv[1:]]
    for book_id in book_ids:
        result = ingest.execute(book_id)
        print(result)


if __name__ == "__main__":
    main()
