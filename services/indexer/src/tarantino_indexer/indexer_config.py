from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IndexerConfig:
    datalake: Path
    datalake_layout: str
    datamarts: Path
    index: str
    metadata: str
    mongo_uri: str
    workload: Path

    @staticmethod
    def from_environment() -> IndexerConfig:
        return IndexerConfig(
            datalake=Path(os.environ.get("TARANTINO_DATALAKE", "datalake")),
            datalake_layout=os.environ.get("TARANTINO_DATALAKE_LAYOUT", "time"),
            datamarts=Path(os.environ.get("TARANTINO_DATAMARTS", "datamarts")),
            index=os.environ.get("TARANTINO_INDEX", "json"),
            metadata=os.environ.get("TARANTINO_METADATA", "sqlite"),
            mongo_uri=os.environ.get(
                "TARANTINO_MONGO_URI", "mongodb://localhost:27017"
            ),
            workload=Path(os.environ.get("TARANTINO_WORKLOAD", "workload")),
        )
