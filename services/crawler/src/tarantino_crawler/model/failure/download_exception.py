from __future__ import annotations

from tarantino_crawler.model.failure.failure_reason import FailureReason


class DownloadException(Exception):
    def __init__(self, reason: FailureReason, message: str):
        super().__init__(message)
        self._reason = reason

    @property
    def reason(self) -> FailureReason:
        return self._reason
