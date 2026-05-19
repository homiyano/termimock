from __future__ import annotations

import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .gui import HTML
from .models import RequestLogEntry, Route
from .store import RouteStore


class MockServer:
    def __init__(self, store: RouteStore, host: str = "127.0.0.1", port: int = 8080, route_file: Path | None = None) -> None:
        self.store = store
        self.host = host
        self.port = port
        self.route_file = route_file
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
        route_file = self.route_file

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
                if request_path.startswith("/_termimock"):
                    self._handle_gui(request_path, send_body)
                    return

                body_json = self._read_json_body()
                match = store.find(self.command, request_path, body_json)
                if match is None:
                    body = b'{"error":"No mock route matched this request"}'
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    if send_body:
                        self.wfile.write(body)
                    store.add_log(RequestLogEntry(self.command, request_path, 404, False))
                    return

                route = match.route
                route_response = store.select_response(route)
                if route.delay_ms:
                    time.sleep(route.delay_ms / 1000)
                rendered_body = render_template(
                    route_response.body,
                    {
                        "method": self.command,
                        "path": request_path,
                        "params": match.params,
                        "query": parse_query(self.path),
                        "body": body_json if isinstance(body_json, dict) else {},
                    },
                )
                body = rendered_body.encode("utf-8")
                self.send_response(route_response.status)
                self.send_header("Content-Type", route_response.content_type)
                for name, value in route_response.headers.items():
                    if name.lower() not in {"content-type", "content-length"}:
                        self.send_header(name, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if send_body:
                    self.wfile.write(body)
                store.add_log(RequestLogEntry(self.command, request_path, route_response.status, True))

            def _read_json_body(self) -> object | None:
                content_length = int(self.headers.get("Content-Length", "0") or "0")
                if content_length <= 0:
                    return None
                raw_body = self.rfile.read(content_length)
                try:
                    return json.loads(raw_body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return None

            def _handle_gui(self, request_path: str, send_body: bool) -> None:
                if self.command == "GET" and request_path in {"/_termimock", "/_termimock/"}:
                    self._send_text(200, "text/html; charset=utf-8", HTML, send_body)
                    return
                if self.command == "GET" and request_path == "/_termimock/api/routes":
                    payload = {
                        "route_file": str(route_file) if route_file else None,
                        "routes": [route.to_dict() for route in store.list_routes()],
                    }
                    self._send_json(200, payload, send_body)
                    return
                if self.command == "GET" and request_path == "/_termimock/api/logs":
                    self._send_json(200, {"logs": [asdict(log) for log in store.list_logs()]}, send_body)
                    return
                if self.command == "POST" and request_path == "/_termimock/api/routes":
                    payload = self._read_json_body()
                    if not isinstance(payload, dict) or not isinstance(payload.get("routes"), list):
                        self._send_json(400, {"error": "Expected JSON object with a routes array"}, send_body)
                        return
                    try:
                        routes = [Route.from_dict(item) for item in payload["routes"]]
                    except (TypeError, ValueError) as exc:
                        self._send_json(400, {"error": str(exc)}, send_body)
                        return
                    store.replace_routes(routes)
                    if route_file:
                        store.save(route_file)
                    self._send_json(200, {"routes": [route.to_dict() for route in store.list_routes()]}, send_body)
                    return
                self._send_json(404, {"error": "Termimock GUI endpoint not found"}, send_body)

            def _send_json(self, status: int, payload: dict[str, Any], send_body: bool) -> None:
                self._send_text(status, "application/json", json.dumps(payload, separators=(",", ":")), send_body)

            def _send_text(self, status: int, content_type: str, text: str, send_body: bool) -> None:
                body = text.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if send_body:
                    self.wfile.write(body)

        return Handler


def parse_query(path: str) -> dict[str, str]:
    return {key: values[-1] for key, values in parse_qs(urlsplit(path).query).items() if values}


def render_template(value: str, context: dict[str, Any]) -> str:
    rendered = value
    for scope in ("params", "query", "body"):
        for key, item in flatten_values(context.get(scope, {})).items():
            rendered = rendered.replace(f"{{{{{scope}.{key}}}}}", str(item))
    rendered = rendered.replace("{{method}}", str(context["method"]))
    rendered = rendered.replace("{{path}}", str(context["path"]))
    return rendered


def flatten_values(data: object, prefix: str = "") -> dict[str, object]:
    if not isinstance(data, dict):
        return {}
    values: dict[str, object] = {}
    for key, value in data.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            values.update(flatten_values(value, name))
        else:
            values[name] = value
    return values
