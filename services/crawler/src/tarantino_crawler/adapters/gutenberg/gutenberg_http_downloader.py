from __future__ import annotations

import ssl

import requests
import truststore
from requests.adapters import HTTPAdapter

from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason
from tarantino_crawler.ports.book_downloader import BookDownloader


class _SystemCertificatesAdapter(HTTPAdapter):
    # Verifies HTTPS against the OS certificate store instead of certifi's bundle, so
    # downloads also work behind antivirus or proxies that inspect HTTPS (e.g. Avast).
    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        super().init_poolmanager(*args, **kwargs)


class GutenbergHttpDownloader(BookDownloader):
    _URL_TEMPLATE = "https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    _USER_AGENT = "query-tarantino/1.0 (ULPGC Big Data course project)"
    _TIMEOUT = 30

    def __init__(self):
        self._session = requests.Session()
        self._session.mount("https://", _SystemCertificatesAdapter())

    def raw_text(self, book_id: int) -> str:
        url = self._URL_TEMPLATE.format(book_id=book_id)
        headers = {"User-Agent": self._USER_AGENT}
        try:
            response = self._session.get(url, headers=headers, timeout=self._TIMEOUT)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                raise DownloadException(
                    FailureReason.NOT_FOUND, f"Book {book_id} not found"
                )
            else:
                raise DownloadException(
                    FailureReason.NETWORK_ERROR, f"HTTP error {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            raise DownloadException(FailureReason.NETWORK_ERROR, f"Network error: {e}")
