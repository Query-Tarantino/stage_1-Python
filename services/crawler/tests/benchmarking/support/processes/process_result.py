from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Dict, List

from services.crawler.tests.benchmarking.support.results.result_row import ResultRow


@dataclass(frozen=True)
class ProcessResult:
    samples: Dict[str, List[float]]
    exact_rows: List[ResultRow]
    sample_rows: List[ResultRow]

    @staticmethod
    def from_json(text: str) -> ProcessResult:
        content = json.loads(text)
        return ProcessResult(
            content["samples"],
            [ResultRow(**row) for row in content["exact_rows"]],
            [ResultRow(**row) for row in content["sample_rows"]],
        )

    def to_json(self) -> str:
        return json.dumps(
            {
                "samples": self.samples,
                "exact_rows": [asdict(row) for row in self.exact_rows],
                "sample_rows": [asdict(row) for row in self.sample_rows],
            }
        )
