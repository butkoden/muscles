from __future__ import annotations

from typing import Any

from .runtime_mode import app_runtime_mode


def _flatten_config(data: Any, prefix: str = "") -> dict[str, Any]:
    if not isinstance(data, dict):
        return {prefix: data} if prefix else {}
    out: dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            out.update(_flatten_config(value, full_key))
        else:
            out[full_key] = value
    return out


def _strategy_name(app) -> list[str]:
    context = getattr(app, "context", None)
    if context is None:
        return []
    strategy = getattr(context, "strategy", None)
    if strategy is None:
        return []
    name = getattr(strategy, "__name__", None)
    if name is None:
        name = strategy.__class__.__name__
    return [name.lower().replace("strategy", "").strip("_")]


def _collect_routes(app) -> list[dict[str, Any]]:
    handlers = getattr(app, "__muscles_routes__", []) or []
    routes = []
    for handler in handlers:
        node = getattr(handler, "node", None)
        routes.append(
            {
                "name": getattr(node, "key", None) or getattr(handler, "__name__", "unknown"),
                "path": getattr(node, "full_route", None),
                "method": getattr(handler, "method", None),
                "handler": f"{getattr(handler, '__module__', '')}.{getattr(handler, '__name__', '')}".strip("."),
            }
        )
    return routes


def _collect_actions(app) -> list[dict[str, Any]]:
    handlers = getattr(app, "__muscles_routes__", []) or []
    actions: list[dict[str, Any]] = []
    for handler in handlers:
        for action in getattr(handler, "actions", []) or []:
            actions.append(
                {
                    "route": getattr(getattr(handler, "node", None), "full_route", None),
                    "action": action,
                    "handler": f"{getattr(handler, '__module__', '')}.{getattr(handler, '__name__', '')}".strip("."),
                }
            )
    return actions


def inspect_application(app=None, include_sensitive: bool = False) -> dict[str, Any]:
    config = getattr(app, "config", None) if app is not None else None
    config_object = getattr(config, "_object", {}) if config is not None else {}
    flattened = _flatten_config(config_object)
    values = flattened if include_sensitive else {}

    return {
        "contract_version": "1",
        "framework": "Muscles",
        "app": app.__class__.__name__ if app is not None else None,
        "runtime_mode": app_runtime_mode(app).value if app is not None else app_runtime_mode().value,
        "strategies": _strategy_name(app) if app is not None else [],
        "routes": _collect_routes(app) if app is not None else [],
        "actions": _collect_actions(app) if app is not None else [],
        "schemas": [],
        "rules": [],
        "cli": [],
        "sql": [],
        "commands": [],
        "warnings": [],
        "config": {
            "known_keys": sorted(flattened.keys()),
            "values": values,
        },
    }
