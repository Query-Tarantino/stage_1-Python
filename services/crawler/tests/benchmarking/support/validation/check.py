from __future__ import annotations


class Check:

    @staticmethod
    def require(condition: bool, failure: str) -> None:
        # A benchmark checks what it measures before measuring it, and its run fails
        # without writing results otherwise (SPEC §11)
        if not condition:
            raise RuntimeError(f"Invalid benchmark result: {failure}")
