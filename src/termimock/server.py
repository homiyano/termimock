from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any
from urllib.parse import urlsplit

from .models import RequestLogEntry
from .store import RouteStore


class MockServer:
    def __init__(self, store: RouteStore, host: str = "127.0.0.1", port: int = 8080) -> None:
        self.store = store
        self.host = host
        self.port = port
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def address(self) -> str:
        if self._httpd:
            host, port = self._httpd.server_address[:2]
            return f"http://{host}:{port}"
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        handler = self._make_handler()
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        store = self.store

        class Handler(BaseHTTPRequestHandler):
            server_version = "Termimock/0.1"

            def do_GET(self) -> None:
                self._handle()

            def do_POST(self) -> None:
                self._handle()

            def do_PUT(self) -> None:
                self._handle()

            def do_PATCH(self) -> None:
                self._handle()

            def do_DELETE(self) -> None:
                self._handle()

            def do_OPTIONS(self) -> None:
                self._handle()

            def do_HEAD(self) -> None:
                self._handle(send_body=False)

            def log_message(self, format: str, *args: Any) -> None:
                return

            def _handle(self, send_body: bool = True) -> None:
                request_path = urlsplit(self.path).path
                route = store.find(self.command, request_path)
                if route is None:
                    body = b'{"error":"No mock route matched this request"}'
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    if send_body:
                        self.wfile.write(body)
                    store.add_log(RequestLogEntry(self.command, request_path, 404, False))
                    return

                body = route.body.encode("utf-8")
                self.send_response(route.status)
                self.send_header("Content-Type", route.content_type)
                for name, value in route.headers.items():
                    if name.lower() not in {"content-type", "content-length"}:
                        self.send_header(name, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if send_body:
                    self.wfile.write(body)
                store.add_log(RequestLogEntry(self.command, request_path, route.status, True))

        return Handler

