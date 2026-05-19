from __future__ import annotations

import json
import random
import threading
from pathlib import Path

from .models import RequestLogEntry, Route, RouteMatch, RouteResponse, normalize_path


class RouteStore:
    def __init__(self, routes: list[Route] | None = None) -> None:
        self._routes = routes or []
        self._logs: list[RequestLogEntry] = []
        self._response_indexes: dict[int, int] = {}
        self._lock = threading.RLock()

    def list_routes(self) -> list[Route]:
        with self._lock:
            return list(self._routes)

    def replace_routes(self, routes: list[Route]) -> None:
        with self._lock:
            self._routes = routes
            self._response_indexes.clear()

    def add_route(self, route: Route) -> None:
        with self._lock:
            self._routes.append(route)

    def update_route(self, index: int, route: Route) -> None:
        with self._lock:
            self._routes[index] = route

    def delete_route(self, index: int) -> None:
        with self._lock:
            self._response_indexes.pop(id(self._routes[index]), None)
            del self._routes[index]

    def find(self, method: str, path: str, body_json: object | None = None) -> RouteMatch | None:
        method = method.upper()
        path = normalize_path(path.split("?", 1)[0])
        with self._lock:
            for route in self._routes:
                if route.enabled and route.method == method:
                    params = match_path(route.path, path)
                    if params is not None and match_body(route.body_match, body_json):
                        return RouteMatch(route, params)
        return None

    def select_response(self, route: Route) -> RouteResponse:
        with self._lock:
            if not route.responses:
                return route.default_response()
            if route.response_mode == "random":
                return random.choice(route.responses)
            if route.response_mode == "cycle":
                route_id = id(route)
                index = self._response_indexes.get(route_id, 0)
                self._response_indexes[route_id] = (index + 1) % len(route.responses)
                return route.responses[index]
            return route.responses[0]

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


def match_path(pattern: str, path: str) -> dict[str, str] | None:
    pattern_parts = normalize_path(pattern).strip("/").split("/")
    path_parts = normalize_path(path).strip("/").split("/")
    if pattern_parts == [""]:
        pattern_parts = []
    if path_parts == [""]:
        path_parts = []
    if len(pattern_parts) != len(path_parts):
        return None

    params: dict[str, str] = {}
    for pattern_part, path_part in zip(pattern_parts, path_parts):
        if pattern_part.startswith(":") and len(pattern_part) > 1:
            params[pattern_part[1:]] = path_part
        elif pattern_part.startswith("{") and pattern_part.endswith("}") and len(pattern_part) > 2:
            params[pattern_part[1:-1]] = path_part
        elif pattern_part != path_part:
            return None
    return params


def match_body(expected: dict[str, object], body_json: object | None) -> bool:
    if not expected:
        return True
    if not isinstance(body_json, dict):
        return False
    for key, expected_value in expected.items():
        if read_json_path(body_json, key) != expected_value:
            return False
    return True


def read_json_path(data: dict[str, object], path: str) -> object | None:
    current: object = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
