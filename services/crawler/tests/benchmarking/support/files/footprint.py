from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Footprint:
    NONE: ClassVar[Footprint]

    files: int
    directories: int
    bytes: int
    allocated_bytes: int


Footprint.NONE = Footprint(0, 0, 0, 0)
