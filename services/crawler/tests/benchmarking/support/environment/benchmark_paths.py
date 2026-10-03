from __future__ import annotations

import os
import re
from pathlib import Path


class BenchmarkPaths:
    # macOS Spotlight skips directories whose name ends in .noindex; elsewhere the name
    # is just a name (SPEC §11)
    SCRATCH_DIRECTORY = "tmp.noindex"

    @staticmethod
    def benchmarks() -> Path:
        return Path(os.environ.get("TARANTINO_BENCHMARKS", "benchmarks"))

    @staticmethod
    def workload() -> Path:
        return Path(os.environ.get("TARANTINO_WORKLOAD", "workload"))

    @staticmethod
    def scratch(name: str) -> Path:
        return BenchmarkPaths.scratch_root() / name

    @staticmethod
    def scratch_root() -> Path:
        return BenchmarkPaths.benchmarks() / BenchmarkPaths.SCRATCH_DIRECTORY

    @staticmethod
    def mongo_uri(database: str) -> str:
        server = os.environ.get("TARANTINO_MONGO_URI", "mongodb://localhost:27017")
        return re.sub("/+$", "", server) + "/" + database
