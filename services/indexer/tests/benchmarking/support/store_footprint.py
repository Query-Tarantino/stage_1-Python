from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StoreFootprint:
    bytes: int
    allocated_bytes: int
    terms: int
