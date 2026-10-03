from __future__ import annotations

from dataclasses import dataclass

from tarantino_query.model.whitespace import JAVA_WHITESPACE


@dataclass(frozen=True)
class WorkloadQuery:
    # A line of queries.txt: <category>: <query> (SPEC §3)
    category: str
    text: str

    @staticmethod
    def parse(line: str) -> WorkloadQuery:
        category, separator, text = line.partition(":")
        if not separator:
            raise ValueError(
                f"A query must be written as <category>: <query>, found: {line}"
            )
        return WorkloadQuery(
            category.strip(JAVA_WHITESPACE), text.strip(JAVA_WHITESPACE)
        )
