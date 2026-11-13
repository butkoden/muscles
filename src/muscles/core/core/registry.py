from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .generator import GeneratorRegistry


@dataclass
class ApplicationRegistry:
    routes: list[Any] = field(default_factory=list)
    schemas: list[Any] = field(default_factory=list)
    rules: list[Any] = field(default_factory=list)
    permissions: dict[str, Any] = field(default_factory=dict)
    permission_policy_extensions: dict[str, dict[str, Any]] = field(default_factory=dict)
    extensions: dict[str, list[Any]] = field(default_factory=dict)
    extension_subscribers: dict[str, list[Any]] = field(default_factory=dict, repr=False)
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

    def add_permission(self, permission: Any) -> None:
        permission_id = getattr(permission, "id", None)
        if not isinstance(permission_id, str) or not permission_id:
            raise ValueError("Permission must have an id")
        if permission_id in self.permissions:
            raise ValueError(f"Duplicate permission: {permission_id}")
        existing = getattr(permission, "policies", {})
        collisions = set(existing) & set(self.permission_policy_extensions.get(permission_id, {}))
        if collisions:
            raise ValueError(f"Duplicate permission policies for {permission_id}: {sorted(collisions)}")
        self.permissions[permission_id] = permission

    def add_permission_policy(self, extension: Any) -> None:
        permission_id = getattr(extension, "permission_id", None)
        policy_id = getattr(extension, "policy_id", None)
        policy = getattr(extension, "policy", None)
        if (not isinstance(permission_id, str) or not permission_id
                or not isinstance(policy_id, str) or not policy_id
                or not callable(getattr(policy, "handler", None))):
            raise ValueError("Invalid permission policy extension")
        existing = self.permission_policy_extensions.get(permission_id, {})
        base = self.permissions.get(permission_id)
        if policy_id in existing or (base is not None and policy_id in getattr(base, "policies", {})):
            raise ValueError(f"Duplicate permission policy: {permission_id}:{policy_id}")
        self.permission_policy_extensions.setdefault(permission_id, {})[policy_id] = policy

    def validate_permission_extensions(self) -> None:
        missing = set(self.permission_policy_extensions) - set(self.permissions)
        if missing:
            raise ValueError(f"Unknown permissions for policy extensions: {sorted(missing)}")

    def add_extension(self, extension: Any) -> None:
        target = getattr(extension, "target", None)
        if not isinstance(target, str) or not target:
            raise ValueError("Package extension must declare a target")
        for subscriber in self.extension_subscribers.get(target, ()):
            subscriber(extension.value)
        self.extensions.setdefault(target, []).append(extension.value)

    def subscribe_extensions(self, target: str, subscriber: Any) -> None:
        if not isinstance(target, str) or not target or not callable(subscriber):
            raise ValueError("Extension target and callable subscriber are required")
        for value in self.extensions.get(target, ()):
            subscriber(value)
        self.extension_subscribers.setdefault(target, []).append(subscriber)

    def unhandled_extensions(self) -> dict[str, int]:
        """Return extension targets that have no installed consumer."""
        return {target: len(values) for target, values in self.extensions.items()
                if not self.extension_subscribers.get(target)}

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
