import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class QueryConfig:
    datamarts: Path
    index: str
    metadata: str
    mongo_uri: str
    workload: Path

    @staticmethod
    def from_environment() -> "QueryConfig":
        return QueryConfig(
            datamarts=Path(os.environ.get("TARANTINO_DATAMARTS", "datamarts")),
            index=os.environ.get("TARANTINO_INDEX", "json"),
            metadata=os.environ.get("TARANTINO_METADATA", "sqlite"),
            mongo_uri=os.environ.get(
                "TARANTINO_MONGO_URI", "mongodb://localhost:27017"
            ),
            workload=Path(os.environ.get("TARANTINO_WORKLOAD", "workload")),
        )
