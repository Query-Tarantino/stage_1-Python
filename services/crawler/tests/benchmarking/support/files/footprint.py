from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Footprint:
    # What a directory tree takes: regular files, directories below the root, the sum
    # of file sizes, and that sum with each file rounded up to whole blocks of its file
    # system (SPEC §11, disk_allocated)
    NONE: ClassVar[Footprint]

    files: int
    directories: int
    bytes: int
    allocated_bytes: int


Footprint.NONE = Footprint(0, 0, 0, 0)
