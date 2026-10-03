from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CrawlerConfig:
    datalake: Path
    datalake_layout: str

    @staticmethod
    def from_environment() -> CrawlerConfig:
        return CrawlerConfig(
            datalake=Path(os.environ.get("TARANTINO_DATALAKE", "datalake")),
            datalake_layout=os.environ.get("TARANTINO_DATALAKE_LAYOUT", "time"),
        )
