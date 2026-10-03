from __future__ import annotations

from typing import Callable, Dict

from tarantino_indexer.adapters.datalake.batch.batch_based_datalake_reader import (
    BatchBasedDatalakeReader,
)
from tarantino_indexer.adapters.datalake.book.book_based_datalake_reader import (
    BookBasedDatalakeReader,
)
from tarantino_indexer.adapters.datalake.time.time_based_datalake_reader import (
    TimeBasedDatalakeReader,
)
from tarantino_indexer.adapters.index.folders.folder_per_term_index_adapter import (
    FolderPerTermIndexAdapter,
)
from tarantino_indexer.adapters.index.json.monolithic_json_index_adapter import (
    MonolithicJsonIndexAdapter,
)
from tarantino_indexer.adapters.index.mongo.mongodb_index_adapter import (
    MongodbIndexAdapter,
)
from tarantino_indexer.adapters.metadata.mongodb_metadata_adapter import (
    MongodbMetadataAdapter,
)
from tarantino_indexer.adapters.metadata.sqlite_metadata_adapter import (
    SqliteMetadataAdapter,
)
from tarantino_indexer.adapters.stopwords.file_stopwords_loader import (
    FileStopwordsLoader,
)
from tarantino_indexer.commands.index_book_command import IndexBookCommand
from tarantino_indexer.indexer_config import IndexerConfig
from tarantino_indexer.model.book.header_parser import HeaderParser
from tarantino_indexer.model.terms.tokenizer import Tokenizer
from tarantino_indexer.ports.datamarts.inverted_index_storage import (
    InvertedIndexStorage,
)
from tarantino_indexer.ports.datamarts.metadata_storage import MetadataStorage
from tarantino_indexer.ports.sources.datalake_reader import DatalakeReader


class IndexerFactory:
    DATALAKE_LAYOUTS: Dict[str, Callable[[IndexerConfig], DatalakeReader]] = {
        "time": lambda config: TimeBasedDatalakeReader(config.datalake),
        "book": lambda config: BookBasedDatalakeReader(config.datalake),
        "batch": lambda config: BatchBasedDatalakeReader(config.datalake),
    }

    INDEX_STRUCTURES: Dict[str, Callable[[IndexerConfig], InvertedIndexStorage]] = {
        "json": lambda config: MonolithicJsonIndexAdapter(
            config.datamarts / "inverted_index.json"
        ),
        "folders": lambda config: FolderPerTermIndexAdapter(
            config.datamarts / "inverted_index"
        ),
        "mongo": lambda config: MongodbIndexAdapter(config.mongo_uri),
    }

    METADATA_BACKENDS: Dict[str, Callable[[IndexerConfig], MetadataStorage]] = {
        "sqlite": lambda config: SqliteMetadataAdapter(
            config.datamarts / "metadata.db"
        ),
        "mongo": lambda config: MongodbMetadataAdapter(config.mongo_uri),
    }

    @staticmethod
    def index_command(config: IndexerConfig) -> IndexBookCommand:
        return IndexBookCommand(
            IndexerFactory.datalake_reader(config),
            HeaderParser(),
            IndexerFactory.tokenizer(config),
            IndexerFactory.inverted_index(config),
            IndexerFactory.metadata(config),
        )

    @staticmethod
    def datalake_reader(config: IndexerConfig) -> DatalakeReader:
        return IndexerFactory._option(
            IndexerFactory.DATALAKE_LAYOUTS, config.datalake_layout, "datalake layout"
        )(config)

    @staticmethod
    def inverted_index(config: IndexerConfig) -> InvertedIndexStorage:
        return IndexerFactory._option(
            IndexerFactory.INDEX_STRUCTURES, config.index, "index structure"
        )(config)

    @staticmethod
    def metadata(config: IndexerConfig) -> MetadataStorage:
        return IndexerFactory._option(
            IndexerFactory.METADATA_BACKENDS, config.metadata, "metadata backend"
        )(config)

    @staticmethod
    def tokenizer(config: IndexerConfig) -> Tokenizer:
        return Tokenizer(
            FileStopwordsLoader(config.workload / "stopwords.txt").stopwords()
        )

    @staticmethod
    def _option(options: dict, name: str, kind: str):
        if name not in options:
            raise ValueError(f"Unknown {kind}: {name}")
        return options[name]
