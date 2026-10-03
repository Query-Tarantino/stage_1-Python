from typing import Callable, Dict, Set, TypeVar

from tarantino_query.adapters.index.folders.folder_per_term_index_reader import (
    FolderPerTermIndexReader,
)
from tarantino_query.adapters.index.json.monolithic_json_index_reader import (
    MonolithicJsonIndexReader,
)
from tarantino_query.adapters.index.mongo.mongodb_index_reader import MongodbIndexReader
from tarantino_query.adapters.metadata.mongodb_metadata_reader import (
    MongodbMetadataReader,
)
from tarantino_query.adapters.metadata.sqlite_metadata_reader import (
    SqliteMetadataReader,
)
from tarantino_query.adapters.stopwords.file_stopwords_loader import FileStopwordsLoader
from tarantino_query.commands.search_command import SearchCommand
from tarantino_query.ports.inverted_index_reader import InvertedIndexReader
from tarantino_query.ports.metadata_reader import MetadataReader
from tarantino_query.query_config import QueryConfig

T = TypeVar("T")


class QueryFactory:
    _INDEX_STRUCTURES: Dict[str, Callable[[QueryConfig], InvertedIndexReader]] = {
        "json": lambda config: MonolithicJsonIndexReader(
            config.datamarts / "inverted_index.json"
        ),
        "folders": lambda config: FolderPerTermIndexReader(
            config.datamarts / "inverted_index"
        ),
        "mongo": lambda config: MongodbIndexReader(config.mongo_uri),
    }

    _METADATA_BACKENDS: Dict[str, Callable[[QueryConfig], MetadataReader]] = {
        "sqlite": lambda config: SqliteMetadataReader(config.datamarts / "metadata.db"),
        "mongo": lambda config: MongodbMetadataReader(config.mongo_uri),
    }

    @staticmethod
    def search_command(config: QueryConfig) -> SearchCommand:
        return SearchCommand(
            QueryFactory.inverted_index(config),
            QueryFactory.metadata(config),
            QueryFactory._stopwords(config),
        )

    @staticmethod
    def inverted_index(config: QueryConfig) -> InvertedIndexReader:
        return QueryFactory._option(
            QueryFactory._INDEX_STRUCTURES, config.index, "index structure"
        )(config)

    @staticmethod
    def metadata(config: QueryConfig) -> MetadataReader:
        return QueryFactory._option(
            QueryFactory._METADATA_BACKENDS, config.metadata, "metadata backend"
        )(config)

    @staticmethod
    def _stopwords(config: QueryConfig) -> Set[str]:
        return FileStopwordsLoader(config.workload / "stopwords.txt").stopwords()

    @staticmethod
    def _option(options: Dict[str, T], name: str, kind: str) -> T:
        option = options.get(name)
        if option is None:
            raise ValueError(f"Unknown {kind}: {name}")
        return option
