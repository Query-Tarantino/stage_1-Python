from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryOutcome:
    recovered: bool
    leftover_files: int
