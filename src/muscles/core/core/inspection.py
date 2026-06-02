from __future__ import annotations

from typing import Any

from .runtime_mode import app_runtime_mode
from .context import Context
from .registry import get_application_registry
from .actions import ApplicationContract


def _serialize_context_transport(transport: Any) -> Any:
    if isinstance(transport, Context):
        return getattr(transport, "_name", None)
    return transport


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


def _collect_contexts(app) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    seen: set[str] = set()

    for cls in app.__class__.mro():
        for name, value in vars(cls).items():
            if not isinstance(value, Context) or not name:
                continue
            if name in seen:
                continue
            seen.add(name)
            strategy = getattr(value, "strategy", None)
            strategy_name = None
            if strategy is not None:
                strategy_name = getattr(strategy, "__name__", None)
                if strategy_name is None and not isinstance(strategy, type):
                    strategy_name = strategy.__class__.__name__
                elif strategy_name is None:
                    strategy_name = str(strategy)
            contexts.append(
                {
                    "name": name,
                    "transport": _serialize_context_transport(getattr(value, "transport", None)),
                    "strategy": strategy_name,
                }
            )

    instance_contexts = vars(app)
    for name, value in instance_contexts.items():
        if not isinstance(value, Context) or name in seen:
            continue
        strategy = getattr(value, "strategy", None)
        strategy_name = None
        if strategy is not None:
            strategy_name = getattr(strategy, "__name__", None)
            if strategy_name is None and not isinstance(strategy, type):
                strategy_name = strategy.__class__.__name__
            elif strategy_name is None:
                strategy_name = str(strategy)
        contexts.append(
            {
                "name": name,
                "transport": _serialize_context_transport(getattr(value, "transport", None)),
                "strategy": strategy_name,
            }
        )

    return contexts


def _collect_routes(app) -> list[dict[str, Any]]:
    registry = get_application_registry(app, create=False)
    handlers = list(getattr(registry, "routes", []) or [])
    if not handlers:
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
    registry = get_application_registry(app, create=False)
    registered_actions = list(getattr(registry, "actions", []) or []) if registry is not None else []
    if registered_actions:
        actions = []
        for action in registered_actions:
            if hasattr(action, "to_contract"):
                actions.append(action.to_contract())
            elif isinstance(action, dict):
                actions.append(action)
            else:
                actions.append({"name": getattr(action, "name", str(action))})
        return actions
    handlers = list(getattr(registry, "routes", []) or [])
    if not handlers:
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

    registry = get_application_registry(app, create=False) if app is not None else None
    contract = ApplicationContract(
        app=app.__class__.__name__ if app is not None else None,
        runtime_mode=app_runtime_mode(app).value if app is not None else app_runtime_mode().value,
        contexts=_collect_contexts(app) if app is not None else [],
        routes=_collect_routes(app) if app is not None else [],
        actions=_collect_actions(app) if app is not None else [],
        schemas=list(getattr(registry, "schemas", []) or []) if registry is not None else [],
        rules=list(getattr(registry, "rules", []) or []) if registry is not None else [],
        cli=list(getattr(registry, "cli", []) or []) if registry is not None else [],
        sql=list(getattr(registry, "sql", []) or []) if registry is not None else [],
        config={
            "known_keys": sorted(flattened.keys()),
            "values": values,
        },
    ).to_contract()
    contract.update({
        "commands": [],
        "warnings": [],
    })
    return contract
