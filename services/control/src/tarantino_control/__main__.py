from __future__ import annotations

import io
import sys
from itertools import takewhile
from typing import List

from tarantino_control.control_config import ControlConfig
from tarantino_control.control_factory import ControlFactory
from tarantino_control.model.step_report import StepReport
from tarantino_crawler.crawler_config import CrawlerConfig
from tarantino_indexer.indexer_config import IndexerConfig


def main(args: List[str]) -> None:
    # UTF-8 lines on every operating system (SPEC §15)
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    # A wrong argument or configuration stops the service before any work (SPEC §15)
    try:
        config = ControlConfig.from_environment()
        candidates = ControlFactory.candidates(
            config, args[0] if len(args) > 0 else None
        )
        pipe = ControlFactory.pipeline(
            config,
            CrawlerConfig.from_environment(),
            IndexerConfig.from_environment(),
            candidates,
        )
    except (OSError, ValueError) as error:
        sys.exit(f"tarantino_control: {error}")

    def step_generator():
        while True:
            yield pipe.run_step()

    for report in takewhile(lambda r: not r.idle(), step_generator()):
        print_report(report)

    print("[CONTROL] Nothing left to do")


def print_report(report: StepReport) -> None:
    print(f"[CONTROL] {report.description()}")


if __name__ == "__main__":
    main(sys.argv[1:])
