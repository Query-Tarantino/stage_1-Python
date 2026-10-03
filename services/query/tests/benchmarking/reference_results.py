from __future__ import annotations

from pathlib import Path
from typing import Dict, List

QUERY_SEPARATOR = "\t"
ID_SEPARATOR = ","


class ReferenceResults:

    @staticmethod
    def read(file: Path) -> Dict[str, List[int]]:
        results = {}
        lines = file.read_text(encoding="utf-8").split("\n")
        for line in filter(None, lines):
            query, ids = line.split(QUERY_SEPARATOR)
            results[query] = [
                int(book_id) for book_id in ids.split(ID_SEPARATOR) if book_id
            ]
        return results

    @staticmethod
    def write(file: Path, results: Dict[str, List[int]]) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            query + QUERY_SEPARATOR + ID_SEPARATOR.join(map(str, ids))
            for query, ids in results.items()
        ]
        file.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
