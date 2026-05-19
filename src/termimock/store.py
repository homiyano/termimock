from __future__ import annotations

import json
import threading
from pathlib import Path

from .models import RequestLogEntry, Route, normalize_path


class RouteStore:
    def __init__(self, routes: list[Route] | None = None) -> None:
        self._routes = routes or []
        self._logs: list[RequestLogEntry] = []
        self._lock = threading.RLock()

    def list_routes(self) -> list[Route]:
        with self._lock:
            return list(self._routes)

    def replace_routes(self, routes: list[Route]) -> None:
        with self._lock:
            self._routes = routes

    def add_route(self, route: Route) -> None:
        with self._lock:
            self._routes.append(route)

    def update_route(self, index: int, route: Route) -> None:
        with self._lock:
            self._routes[index] = route

    def delete_route(self, index: int) -> None:
        with self._lock:
            del self._routes[index]

    def find(self, method: str, path: str) -> Route | None:
        method = method.upper()
        path = normalize_path(path.split("?", 1)[0])
        with self._lock:
            for route in self._routes:
                if route.enabled and route.method == method and route.path == path:
                    return route
        return None

    def add_log(self, entry: RequestLogEntry) -> None:
        with self._lock:
            self._logs.insert(0, entry)
            del self._logs[100:]

    def list_logs(self) -> list[RequestLogEntry]:
        with self._lock:
            return list(self._logs)

    def load(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        routes = [Route.from_dict(item) for item in data.get("routes", [])]
        self.replace_routes(routes)

    def save(self, path: Path) -> None:
        payload = {"routes": [route.to_dict() for route in self.list_routes()]}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

