from __future__ import annotations

from enum import Enum, auto


class FailureReason(Enum):
    NOT_FOUND = auto()
    NETWORK_ERROR = auto()
    MISSING_MARKERS = auto()
    STORAGE_ERROR = auto()
