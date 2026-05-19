from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD")


@dataclass(slots=True)
class Route:
    method: str
    path: str
    status: int = 200
    content_type: str = "application/json"
    headers: dict[str, str] = field(default_factory=dict)
    body: str = "{}"
    enabled: bool = True

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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Route":
        return cls(
            method=str(data.get("method", "GET")),
            path=str(data.get("path", "/")),
            status=int(data.get("status", 200)),
            content_type=str(data.get("content_type", data.get("contentType", "application/json"))),
            headers=dict(data.get("headers", {})),
            body=str(data.get("body", "{}")),
            enabled=bool(data.get("enabled", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def label(self) -> str:
        state = "on" if self.enabled else "off"
        return f"{state:>3} {self.method:<7} {self.path:<28} {self.status:<3} {self.content_type}"


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

