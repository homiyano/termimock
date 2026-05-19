from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD")
RESPONSE_MODES = ("first", "cycle", "random")


@dataclass(slots=True)
class RouteResponse:
    status: int = 200
    content_type: str = "application/json"
    headers: dict[str, str] = field(default_factory=dict)
    body: str = "{}"

    def __post_init__(self) -> None:
        if not 100 <= int(self.status) <= 599:
            raise ValueError("Status must be a valid HTTP status code")
        self.status = int(self.status)
        self.content_type = self.content_type.strip() or "text/plain"
        self.headers = {str(k): str(v) for k, v in self.headers.items()}
        self.body = str(self.body)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteResponse":
        return cls(
            status=int(data.get("status", 200)),
            content_type=str(data.get("content_type", data.get("contentType", "application/json"))),
            headers=dict(data.get("headers", {})),
            body=str(data.get("body", "{}")),
        )


@dataclass(slots=True)
class Route:
    method: str
    path: str
    status: int = 200
    content_type: str = "application/json"
    headers: dict[str, str] = field(default_factory=dict)
    body: str = "{}"
    enabled: bool = True
    delay_ms: int = 0
    responses: list[RouteResponse] = field(default_factory=list)
    response_mode: str = "first"
    body_match: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.method = self.method.upper().strip()
        if self.method not in HTTP_METHODS:
            raise ValueError(f"Unsupported HTTP method: {self.method}")
        self.path = normalize_path(self.path)
        if not 100 <= int(self.status) <= 599:
            raise ValueError("Status must be a valid HTTP status code")
        self.status = int(self.status)
        self.content_type = self.content_type.strip() or "text/plain"
        self.headers = {str(k): str(v) for k, v in self.headers.items()}
        self.body = str(self.body)
        self.enabled = bool(self.enabled)
        self.delay_ms = max(0, int(self.delay_ms))
        self.responses = [response if isinstance(response, RouteResponse) else RouteResponse.from_dict(response) for response in self.responses]
        self.response_mode = self.response_mode.strip().lower()
        if self.response_mode not in RESPONSE_MODES:
            raise ValueError(f"Unsupported response mode: {self.response_mode}")
        self.body_match = dict(self.body_match)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Route":
        body_match = data.get("body_match", data.get("bodyMatch", data.get("match_json", {})))
        if not body_match and isinstance(data.get("match"), dict):
            body_match = data["match"].get("json", {})
        return cls(
            method=str(data.get("method", "GET")),
            path=str(data.get("path", "/")),
            status=int(data.get("status", 200)),
            content_type=str(data.get("content_type", data.get("contentType", "application/json"))),
            headers=dict(data.get("headers", {})),
            body=str(data.get("body", "{}")),
            enabled=bool(data.get("enabled", True)),
            delay_ms=int(data.get("delay_ms", data.get("delayMs", 0))),
            responses=[RouteResponse.from_dict(item) for item in data.get("responses", [])],
            response_mode=str(data.get("response_mode", data.get("responseMode", "first"))),
            body_match=dict(body_match),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def label(self) -> str:
        state = "on" if self.enabled else "off"
        delay = f"{self.delay_ms}ms" if self.delay_ms else "-"
        variants = f"{self.response_mode}:{len(self.responses)}" if self.responses else "-"
        return f"{state:>3} {self.method:<7} {self.path:<28} {self.status:<3} {delay:<7} {variants:<9} {self.content_type}"

    def default_response(self) -> RouteResponse:
        return RouteResponse(self.status, self.content_type, dict(self.headers), self.body)


@dataclass(slots=True)
class RouteMatch:
    route: Route
    params: dict[str, str]


@dataclass(slots=True)
class RequestLogEntry:
    method: str
    path: str
    status: int
    matched: bool

    def label(self) -> str:
        hit = "hit" if self.matched else "miss"
        return f"{self.method:<7} {self.path:<34} {self.status:<3} {hit}"


def normalize_path(path: str) -> str:
    path = path.strip() or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return path
