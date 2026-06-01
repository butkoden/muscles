from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApplicationRegistry:
    routes: list[Any] = field(default_factory=list)
    schemas: list[Any] = field(default_factory=list)
    rules: list[Any] = field(default_factory=list)
    events: dict[str, list[Any]] = field(default_factory=dict)
    cli: list[Any] = field(default_factory=list)
    actions: list[Any] = field(default_factory=list)
    sql: list[Any] = field(default_factory=list)
    openapi: dict[str, Any] = field(default_factory=dict)

    def add_route(self, route: Any) -> None:
        self.routes.append(route)

    def add_schema(self, schema: Any) -> None:
        self.schemas.append(schema)

    def add_rule(self, rule: Any) -> None:
        self.rules.append(rule)

    def add_cli(self, command: Any) -> None:
        self.cli.append(command)

    def add_action(self, action: Any) -> None:
        self.actions.append(action)

    def add_sql(self, item: Any) -> None:
        self.sql.append(item)

    def emit_event(self, key: str, payload: Any) -> None:
        if key not in self.events:
            self.events[key] = []
        self.events[key].append(payload)

    def get_events(self, key: str) -> list[Any]:
        return list(self.events.get(key, []))


_fallback_registry = ApplicationRegistry()


def get_application_registry(app=None, create: bool = True) -> ApplicationRegistry:
    if app is None:
        return _fallback_registry
    registry = getattr(app, "__muscles_registry__", None)
    if registry is None and create:
        registry = ApplicationRegistry()
        setattr(app, "__muscles_registry__", registry)
    return registry or _fallback_registry
