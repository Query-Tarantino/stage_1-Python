from __future__ import annotations

import email.utils
import http.client
import itertools
import re
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import truststore

from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason
from tarantino_crawler.model.whitespace import JAVA_WHITESPACE
from tarantino_crawler.ports.book_downloader import BookDownloader


class _MirrorRedirects(urllib.request.HTTPRedirectHandler):
    max_redirections = 5

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl).hostname
        if target != urllib.parse.urlsplit(req.full_url).hostname:
            fp.close()
            raise DownloadException(
                FailureReason.NETWORK_ERROR,
                f"{req.full_url} was redirected to {target}, which is not the mirror",
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class GutenbergHttpDownloader(BookDownloader):
    URL_TEMPLATE = "https://mirror.cs.odu.edu/gutenberg-epub/{book_id}/pg{book_id}.txt"
    USER_AGENT = "query-tarantino/1.0 (ULPGC Big Data course project)"
    TIMEOUT = 30
    BUSY = {429, 503}
    MAX_RETRIES = 5
    FIRST_WAIT = timedelta(seconds=1)
    LONGEST_WAIT = timedelta(minutes=5)
    SECONDS = re.compile(r"[0-9]{1,9}")

    def __init__(
        self,
        url_template: str = URL_TEMPLATE,
        clock: Optional[Callable[[], datetime]] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._url_template = url_template
        self._clock = clock if clock else lambda: datetime.now(timezone.utc)
        self._sleep = sleep
        self._paused_until = datetime.fromtimestamp(0, timezone.utc)
        self._pause_lock = threading.Lock()
        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=context), _MirrorRedirects()
        )

    def raw_text(self, book_id: int) -> str:
        url = self._url_template.format(book_id=book_id)
        for retries in itertools.count():
            self._wait_for_the_mirror()
            response = self._send(url, book_id)
            try:
                if response.code not in self.BUSY:
                    return self._body(response, book_id)
                wait = self._retry_after(response)
            finally:
                response.close()
            if wait is None:
                wait = self.FIRST_WAIT * (1 << retries)
            if retries == self.MAX_RETRIES or wait > self.LONGEST_WAIT:
                raise DownloadException(
                    FailureReason.NETWORK_ERROR,
                    f"HTTP {response.code} for book {book_id}: the mirror is busy",
                )
            self._pause_the_mirror(wait)

    def _wait_for_the_mirror(self) -> None:
        left = (self._paused_until - self._clock()).total_seconds()
        if left > 0:
            self._sleep(left)

    def _pause_the_mirror(self, wait: timedelta) -> None:
        until = self._clock() + wait
        with self._pause_lock:
            self._paused_until = max(self._paused_until, until)

    def _send(self, url: str, book_id: int):
        request = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
        try:
            return self._opener.open(request, timeout=self.TIMEOUT)
        except urllib.error.HTTPError as answer:
            return answer
        except (urllib.error.URLError, http.client.HTTPException, OSError) as error:
            raise DownloadException(
                FailureReason.NETWORK_ERROR,
                f"Could not download book {book_id}: {error}",
            ) from error

    def _retry_after(self, response) -> Optional[timedelta]:
        retry_after = response.headers.get("Retry-After")
        if retry_after is None:
            return None
        retry_after = retry_after.strip(JAVA_WHITESPACE)
        if self.SECONDS.fullmatch(retry_after):
            return timedelta(seconds=int(retry_after))
        try:
            date = email.utils.parsedate_to_datetime(retry_after)
        except (TypeError, ValueError):
            return None
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return max(date - self._clock(), timedelta(0))

    @staticmethod
    def _body(response, book_id: int) -> str:
        if response.code == 200:
            try:
                return response.read().decode("utf-8", errors="replace")
            except (http.client.HTTPException, OSError) as error:
                raise DownloadException(
                    FailureReason.NETWORK_ERROR,
                    f"Could not download book {book_id}: {error}",
                ) from error
        if response.code == 404:
            raise DownloadException(
                FailureReason.NOT_FOUND, f"Book {book_id} not found"
            )
        raise DownloadException(
            FailureReason.NETWORK_ERROR, f"HTTP {response.code} for book {book_id}"
        )
