from __future__ import annotations

import hashlib
from pathlib import Path


class TermFiles:
    # Term file names that stay distinct on file systems that ignore case or
    # normalization (APFS, NTFS): ASCII lowercase letters are kept and every other
    # UTF-8 byte is written as %XX, so no two terms share a name; names longer than
    # 200 characters become the SHA-256 of the term (SPEC §8.1)
    SUFFIX = ".txt"
    MAX_NAME_LENGTH = 200
    HASH_PREFIX = "#"
    BYTE_NAMES = [
        chr(byte) if ord("a") <= byte <= ord("z") else f"%{byte:02X}"
        for byte in range(256)
    ]

    @staticmethod
    def file(root: Path, term: str) -> Path:
        return (
            root
            / TermFiles._encoded(term[0])
            / (TermFiles._name(term) + TermFiles.SUFFIX)
        )

    @staticmethod
    def _name(term: str) -> str:
        encoded = TermFiles._encoded(term)
        if len(encoded) <= TermFiles.MAX_NAME_LENGTH:
            return encoded
        return TermFiles.HASH_PREFIX + hashlib.sha256(term.encode("utf-8")).hexdigest()

    @staticmethod
    def _encoded(text: str) -> str:
        return "".join(TermFiles.BYTE_NAMES[byte] for byte in text.encode("utf-8"))
