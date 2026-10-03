from __future__ import annotations

import os
import shutil
import stat
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from services.crawler.tests.benchmarking.support.files.footprint import Footprint


class Directories:

    @staticmethod
    def delete(root: Path) -> None:
        directories, files = Directories._tree(root)
        with ThreadPoolExecutor() as pool:
            list(pool.map(os.unlink, files))
        for directory in reversed(directories):
            os.rmdir(directory)

    @staticmethod
    def copy(source: Path, target: Path) -> None:
        directories, files = Directories._tree(source)
        for directory in directories:
            os.makedirs(target / os.path.relpath(directory, source), exist_ok=True)
        with ThreadPoolExecutor() as pool:
            list(
                pool.map(
                    lambda file: shutil.copyfile(
                        file, target / os.path.relpath(file, source)
                    ),
                    files,
                )
            )

    @staticmethod
    def file_count(root: Path, keep: Optional[Callable[[Path], bool]] = None) -> int:
        return sum(
            1
            for directory, _, names in os.walk(root)
            for name in names
            if os.path.isfile(path := os.path.join(directory, name))
            and (keep is None or keep(Path(path)))
        )

    @staticmethod
    def footprint(root: Path) -> Footprint:
        if not root.exists():
            return Footprint.NONE
        block = os.statvfs(root).f_frsize
        files = directories = size = allocated = 0
        for directory, subdirectories, names in os.walk(root):
            directories += len(subdirectories)
            for name in names:
                attributes = os.lstat(os.path.join(directory, name))
                if stat.S_ISREG(attributes.st_mode):
                    files += 1
                    size += attributes.st_size
                    allocated += -(-attributes.st_size // block) * block
        return Footprint(files, directories, size, allocated)

    @staticmethod
    def _tree(root: Path) -> Tuple[List[str], List[str]]:
        if root.is_file() or root.is_symlink():
            return [], [str(root)]
        directories: List[str] = []
        files: List[str] = []
        for directory, _, names in os.walk(root):
            directories.append(directory)
            files.extend(os.path.join(directory, name) for name in names)
        return directories, files
