"""Helpers for projecting Muscles schemas to OpenAPI Schema Objects."""

from __future__ import annotations

from typing import Any


_TYPE_MAP = {
    "array": "array",
    "big_integer": "integer",
    "binary": "string",
    "boolean": "boolean",
    "date": "string",
    "date_time": "string",
    "double": "number",
    "enum": "string",
    "file": "string",
    "float": "number",
    "integer": "integer",
    "json": "object",
    "key": "integer",
    "number": "number",
    "small_integer": "integer",
    "string": "string",
    "time": "string",
    "timestamp": "string",
    "uuid": "string",
    "value_object": "string",
}

_FORMAT_MAP = {
    "binary": "binary",
    "date": "date",
    "date_time": "date-time",
    "email": "email",
    "time": "time",
    "timestamp": "date-time",
    "uuid": "uuid",
}


def to_openapi_schema(value: Any) -> Any:
    """Return a JSON-serializable OpenAPI Schema/Reference projection.

    The regular ``dump`` methods are also used as the framework's historical
    introspection format and intentionally contain implementation metadata.
    OpenAPI documents must not expose that metadata, so endpoint generators use
    this explicit projection.
    """

    if isinstance(value, list):
        return [to_openapi_schema(item) for item in value]
    if not isinstance(value, dict):
        return value

    if "$ref" in value:
        return {"$ref": value["$ref"]}

    if len(value) == 1:
        name, model_schema = next(iter(value.items()))
        if isinstance(model_schema, dict) and model_schema.get("type") == "object":
            return {"$ref": f"#/components/schemas/{name}"}
        if isinstance(model_schema, dict) and (
            "data_type" in model_schema or "class" in model_schema
        ):
            return {
                "type": "object",
                "properties": {name: to_openapi_schema(model_schema)},
            }

    data_type = value.get("data_type")
    if data_type is not None or "class" in value:
        result: dict[str, Any] = {"type": _TYPE_MAP.get(data_type, value.get("type", "object"))}
        data_format = value.get("data_format") or data_type
        if data_format in _FORMAT_MAP:
            result["format"] = _FORMAT_MAP[data_format]
        if value.get("enum") is not None:
            result["enum"] = list(value["enum"])
        if value.get("items"):
            items = value["items"]
            if isinstance(items, list):
                items = items[0] if items else {}
            result["items"] = to_openapi_schema(items)
        for source, target in (
            ("pattern", "pattern"),
            ("minItems", "minItems"),
            ("maxItems", "maxItems"),
            ("uniqueItems", "uniqueItems"),
            ("min_length", "minLength"),
            ("max_length", "maxLength"),
        ):
            if value.get(source) is not None and not (
                target == "pattern" and result["type"] != "string"
            ):
                result[target] = value[source]
        return result

    return {
        key: to_openapi_schema(item)
        for key, item in value.items()
        if item is not None
    }
