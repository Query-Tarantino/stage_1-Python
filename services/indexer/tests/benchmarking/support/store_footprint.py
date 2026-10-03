from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StoreFootprint:
    # Disk taken by an inverted index, logical and in whole blocks, and its number of
    # distinct terms
    bytes: int
    allocated_bytes: int
    terms: int
