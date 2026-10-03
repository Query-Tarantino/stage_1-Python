from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ControlConfig:
    control: Path
    workload: Path

    @staticmethod
    def from_environment() -> ControlConfig:
        return ControlConfig(
            control=Path(os.environ.get("TARANTINO_CONTROL", "control")),
            workload=Path(os.environ.get("TARANTINO_WORKLOAD", "workload")),
        )
