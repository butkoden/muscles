from __future__ import annotations


FIELD_TYPE_MAP = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def pydantic_available() -> bool:
    try:
        import pydantic  # noqa: F401

        return True
    except Exception:
        return False


def to_json_schema(model_cls_or_instance) -> dict:
    model = model_cls_or_instance if not isinstance(model_cls_or_instance, type) else model_cls_or_instance()
    if not hasattr(model, "columns"):
        raise TypeError("Muscles model with columns is required")

    properties = {}
    for name, column in model.columns.items():
        if getattr(column, "column_name", None) is None:
            column.column_name = name
        properties[name] = column.field_type.dump()
    return {
        model.__class__.__name__: {
            "type": "object",
            "properties": properties,
        }
    }


def to_pydantic_model(model_cls):
    try:
        from pydantic import create_model
    except Exception as exc:
        raise ImportError("Pydantic is not installed. Install it to use bridge features.") from exc

    schema = to_json_schema(model_cls)
    model_name = model_cls.__name__
    properties = schema.get(model_name, {}).get("properties", {})
    fields = {}
    for name, meta in properties.items():
        py_type = FIELD_TYPE_MAP.get(meta.get("type", "string"), str)
        fields[name] = (py_type, None)
    return create_model(f"{model_name}Pydantic", **fields)


def from_pydantic_instance(model_cls, pydantic_instance):
    if not hasattr(pydantic_instance, "model_dump"):
        raise TypeError("Pydantic v2 instance with model_dump() is required")
    return model_cls(**pydantic_instance.model_dump())
