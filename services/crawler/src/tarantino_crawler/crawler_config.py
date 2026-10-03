from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tarantino_crawler.model.whitespace import JAVA_WHITESPACE


@dataclass(frozen=True)
class CrawlerConfig:
    datalake: Path
    datalake_layout: str
    # The local Gutenberg mirror to read books from, or None to download them over HTTP
    mirror: Optional[Path] = None

    @staticmethod
    def from_environment() -> CrawlerConfig:
        mirror = os.environ.get("TARANTINO_MIRROR", "")
        return CrawlerConfig(
            datalake=Path(os.environ.get("TARANTINO_DATALAKE", "datalake")),
            datalake_layout=os.environ.get("TARANTINO_DATALAKE_LAYOUT", "time"),
            mirror=Path(mirror) if mirror.strip(JAVA_WHITESPACE) else None,
        )
