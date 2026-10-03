from __future__ import annotations

from typing import Protocol, Set


class StopwordsLoader(Protocol):
    def stopwords(self) -> Set[str]: ...
