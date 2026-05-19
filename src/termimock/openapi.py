from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Route


OPENAPI_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def import_openapi(path: Path) -> list[Route]:
    data = json.loads(path.read_text(encoding="utf-8"))
    routes: list[Route] = []
    for route_path, path_item in data.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in OPENAPI_METHODS or not isinstance(operation, dict):
                continue
            status, content_type, body = response_from_operation(operation)
            routes.append(
                Route(
                    method.upper(),
                    route_path,
                    status=status,
                    content_type=content_type,
                    body=body,
                )
            )
    return routes


def response_from_operation(operation: dict[str, Any]) -> tuple[int, str, str]:
    responses = operation.get("responses", {})
    if not isinstance(responses, dict) or not responses:
        return 200, "application/json", "{}"

    status_key = pick_status(responses)
    response = responses.get(status_key, {})
    status = int(status_key) if str(status_key).isdigit() else 200
    if not isinstance(response, dict):
        return status, "application/json", "{}"

    content = response.get("content", {})
    if not isinstance(content, dict) or not content:
        return status, "application/json", "{}"

    content_type = "application/json" if "application/json" in content else next(iter(content))
    media_type = content.get(content_type, {})
    example = example_from_media_type(media_type)
    return status, content_type, json.dumps(example, separators=(",", ":"))


def pick_status(responses: dict[str, Any]) -> str:
    for key in responses:
        if str(key).startswith("2"):
            return str(key)
    return str(next(iter(responses)))


def example_from_media_type(media_type: object) -> object:
    if not isinstance(media_type, dict):
        return {}
    if "example" in media_type:
        return media_type["example"]
    examples = media_type.get("examples")
    if isinstance(examples, dict) and examples:
        first_example = next(iter(examples.values()))
        if isinstance(first_example, dict) and "value" in first_example:
            return first_example["value"]
    schema = media_type.get("schema")
    return example_from_schema(schema)


def example_from_schema(schema: object) -> object:
    if not isinstance(schema, dict):
        return {}
    if "example" in schema:
        return schema["example"]
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            return {}
        return {key: example_from_schema(value) for key, value in properties.items()}
    if schema_type == "array":
        return [example_from_schema(schema.get("items", {}))]
    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0.0
    if schema_type == "boolean":
        return False
    if schema_type == "string":
        return "string"
    return {}
