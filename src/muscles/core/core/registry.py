from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .generator import GeneratorRegistry


@dataclass
class ApplicationRegistry:
    routes: list[Any] = field(default_factory=list)
    schemas: list[Any] = field(default_factory=list)
    rules: list[Any] = field(default_factory=list)
    events: dict[str, list[Any]] = field(default_factory=dict)
    cli: list[Any] = field(default_factory=list)
    actions: list[Any] = field(default_factory=list)
    sql: list[Any] = field(default_factory=list)
    packages: dict[str, dict[str, Any]] = field(default_factory=dict)
    inspection_providers: dict[str, Any] = field(default_factory=dict)
    doctor_providers: dict[str, Any] = field(default_factory=dict)
    generator_registry: GeneratorRegistry = field(default_factory=GeneratorRegistry)
    openapi: dict[str, Any] = field(default_factory=dict)
    _actions_by_name: dict[str, Any] = field(default_factory=dict)

    def add_route(self, route: Any) -> None:
        self.routes.append(route)

    def add_schema(self, schema: Any) -> None:
        self.schemas.append(schema)

    def add_rule(self, rule: Any) -> None:
        self.rules.append(rule)

    def add_cli(self, command: Any) -> None:
        self.cli.append(command)

    def add_action(self, action: Any) -> None:
        name = getattr(action, "name", None)
        if name:
            previous = self._actions_by_name.get(name)
            if previous in self.actions:
                self.actions.remove(previous)
            self._actions_by_name[name] = action
        self.actions.append(action)

    def get_action(self, name: str) -> Any | None:
        if name in self._actions_by_name:
            return self._actions_by_name[name]
        for action in self.actions:
            if getattr(action, "name", None) == name:
                self._actions_by_name[name] = action
                return action
        return None

    def add_sql(self, item: Any) -> None:
        self.sql.append(item)

    def add_package(self, namespace: str, contract: dict[str, Any]) -> None:
        self.packages[namespace] = dict(contract)

    def add_inspection_provider(self, namespace: str, provider: Any) -> None:
        self.inspection_providers[namespace] = provider

    def add_doctor_provider(self, namespace: str, provider: Any) -> None:
        self.doctor_providers[namespace] = provider

    def add_generator_provider(self, provider: Any) -> None:
        self.generator_registry.register(provider)

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
