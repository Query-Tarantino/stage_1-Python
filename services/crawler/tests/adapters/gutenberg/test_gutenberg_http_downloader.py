import threading
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from tarantino_crawler.adapters.gutenberg.gutenberg_http_downloader import (
    GutenbergHttpDownloader,
)
from tarantino_crawler.model.failure.download_exception import DownloadException
from tarantino_crawler.model.failure.failure_reason import FailureReason

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
TEXT = "Café *** START"


class Mirror(BaseHTTPRequestHandler):
    # Answers with the statuses and headers queued in answers, and 200 with TEXT when no
    # answer is left
    def do_GET(self):
        self.server.requests.append(self.path)
        self.server.user_agents.append(self.headers["User-Agent"])
        status, headers = (
            self.server.answers.popleft() if self.server.answers else (200, {})
        )
        body = TEXT.encode("utf-8") if status == 200 else b""
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def serve() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Mirror)
    server.requests, server.user_agents, server.answers = [], [], deque()
    # Polled often, so that shutting the server down after each test is quick
    serving = threading.Thread(target=server.serve_forever, args=(0.01,), daemon=True)
    serving.start()
    return server


@pytest.fixture
def mirror():
    server = serve()
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def waits() -> list:
    return []


def downloader_of(url_template: str, waits: list) -> GutenbergHttpDownloader:
    return GutenbergHttpDownloader(url_template, clock=lambda: NOW, sleep=waits.append)


@pytest.fixture
def downloader(mirror, waits) -> GutenbergHttpDownloader:
    port = mirror.server_address[1]
    template = f"http://127.0.0.1:{port}/gutenberg-epub/{{book_id}}/pg{{book_id}}.txt"
    return downloader_of(template, waits)


def failure(downloader: GutenbergHttpDownloader, book_id: int = 1342) -> FailureReason:
    with pytest.raises(DownloadException) as error:
        downloader.raw_text(book_id)
    return error.value.reason


def test_returns_the_body_decoded_as_utf8(downloader, mirror):
    assert downloader.raw_text(1342) == TEXT
    assert mirror.requests == ["/gutenberg-epub/1342/pg1342.txt"]


def test_tells_the_mirror_who_is_downloading(downloader, mirror):
    downloader.raw_text(1342)

    assert mirror.user_agents == ["query-tarantino/1.0 (ULPGC Big Data course project)"]


def test_maps_missing_books_to_not_found(downloader, mirror):
    mirror.answers.append((404, {}))

    assert failure(downloader) == FailureReason.NOT_FOUND


def test_maps_server_errors_to_network_error_without_retrying(downloader, mirror):
    mirror.answers.append((500, {}))

    assert failure(downloader) == FailureReason.NETWORK_ERROR
    assert len(mirror.requests) == 1


def test_maps_unreachable_servers_to_network_error(waits):
    unreachable = downloader_of("http://127.0.0.1:1/{book_id}/{book_id}.txt", waits)

    assert failure(unreachable, 1) == FailureReason.NETWORK_ERROR


def test_retries_a_busy_mirror_after_the_wait_it_asks_for(downloader, mirror, waits):
    mirror.answers.append((429, {"Retry-After": "120"}))

    assert downloader.raw_text(1342) == TEXT
    assert waits == [120]
    assert len(mirror.requests) == 2


def test_reads_the_wait_as_an_http_date(downloader, mirror, waits):
    mirror.answers.append((503, {"Retry-After": "Thu, 01 Oct 2026 12:01:30 GMT"}))

    assert downloader.raw_text(1342) == TEXT
    assert waits == [90]


def test_doubles_the_wait_when_the_mirror_does_not_say_how_long(
    downloader, mirror, waits
):
    mirror.answers.extend([(503, {}), (503, {}), (429, {})])

    assert downloader.raw_text(1342) == TEXT
    assert waits == [1, 2, 4]


def test_makes_every_download_wait_while_the_mirror_is_busy(downloader, mirror, waits):
    mirror.answers.append((429, {"Retry-After": "60"}))
    downloader.raw_text(1342)
    # The clock stands still, so the second download starts while the mirror still asks
    # to wait
    downloader.raw_text(84)

    assert waits == [60, 60]


def test_gives_up_when_the_mirror_stays_busy(downloader, mirror):
    mirror.answers.extend([(429, {"Retry-After": "0"})] * 6)

    assert failure(downloader) == FailureReason.NETWORK_ERROR
    assert len(mirror.requests) == 6


def test_gives_up_when_the_mirror_asks_to_wait_too_long(downloader, mirror, waits):
    mirror.answers.append((503, {"Retry-After": "3600"}))

    assert failure(downloader) == FailureReason.NETWORK_ERROR
    assert waits == []
    assert len(mirror.requests) == 1


def test_follows_redirects_within_the_mirror(downloader, mirror):
    mirror.answers.append((302, {"Location": "/moved/pg1342.txt"}))

    assert downloader.raw_text(1342) == TEXT
    assert mirror.requests == ["/gutenberg-epub/1342/pg1342.txt", "/moved/pg1342.txt"]


def test_follows_at_most_five_redirects(downloader, mirror):
    mirror.answers.extend([(302, {"Location": f"/moved/{hop}"}) for hop in range(6)])

    assert failure(downloader) == FailureReason.NETWORK_ERROR
    assert len(mirror.requests) == 6


def test_never_follows_a_redirect_to_another_host(downloader, mirror):
    other_host = serve()
    try:
        port = other_host.server_address[1]
        location = f"http://localhost:{port}/cache/epub/1342/pg1342.txt"
        mirror.answers.append((301, {"Location": location}))

        assert failure(downloader) == FailureReason.NETWORK_ERROR
        assert other_host.requests == []
    finally:
        other_host.shutdown()
        other_host.server_close()
