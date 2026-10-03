from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from tarantino_control.model.whitespace import JAVA_WHITESPACE


@dataclass(frozen=True)
class ControlConfig:
    control: Path
    workload: Path
    parallel_downloads: int = 8
    index_batch: int = 100

    @staticmethod
    def from_environment() -> ControlConfig:
        return ControlConfig(
            control=Path(os.environ.get("TARANTINO_CONTROL", "control")),
            workload=Path(os.environ.get("TARANTINO_WORKLOAD", "workload")),
            parallel_downloads=ControlConfig.positive_integer(
                "TARANTINO_PARALLEL_DOWNLOADS",
                os.environ.get("TARANTINO_PARALLEL_DOWNLOADS", "8"),
            ),
            index_batch=ControlConfig.positive_integer(
                "TARANTINO_INDEX_BATCH", os.environ.get("TARANTINO_INDEX_BATCH", "100")
            ),
        )

    @staticmethod
    def positive_integer(name: str, value: str) -> int:
        try:
            number = int(value.strip(JAVA_WHITESPACE))
            if number > 0:
                return number
        except ValueError:
            pass
        raise ValueError(f"Unknown {name}: {value} (expected a positive integer)")
