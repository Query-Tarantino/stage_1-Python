from __future__ import annotations


class Check:

    @staticmethod
    def require(condition: bool, failure: str) -> None:
        if not condition:
            raise RuntimeError(f"Invalid benchmark result: {failure}")
