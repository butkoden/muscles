from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable


Provider = Callable[..., Any] | type | Any


@dataclass(frozen=True)
class DependencyRegistration:
    interface: type
    provider: Provider
    scope: str
    args: tuple
    kwargs: dict


class DependencyScope:
    def __init__(self, container: "DependencyContainer"):
        self.container = container
        self._instances = {}

    def resolve(self, interface: type):
        return self.container.resolve(interface, scope=self)


class DependencyContainer:
    """Small app/request scoped dependency container for framework integrations."""

    APP = "app"
    REQUEST = "request"
    TRANSIENT = "transient"
    _VALID_SCOPES = {APP, REQUEST, TRANSIENT}

    def __init__(self):
        self._registrations: dict[type, DependencyRegistration] = {}
        self._app_instances = {}

    def register(self, interface: type, provider: Provider, *args, scope: str = APP, **kwargs):
        if scope not in self._VALID_SCOPES:
            raise ValueError(f"Unsupported dependency scope `{scope}`")
        self._registrations[interface] = DependencyRegistration(
            interface=interface,
            provider=provider,
            scope=scope,
            args=args,
            kwargs=dict(kwargs),
        )
        self._app_instances.pop(interface, None)
        return provider

    def create_scope(self) -> DependencyScope:
        return DependencyScope(self)

    def resolve(self, interface: type, scope: DependencyScope | None = None):
        if interface not in self._registrations:
            raise KeyError(f"Dependency {interface.__name__} not registered")

        registration = self._registrations[interface]
        if registration.scope == self.TRANSIENT:
            return self._build(registration)

        if registration.scope == self.REQUEST:
            if scope is None:
                return self._build(registration)
            if interface not in scope._instances:
                scope._instances[interface] = self._build(registration)
            return scope._instances[interface]

        if interface not in self._app_instances:
            self._app_instances[interface] = self._build(registration)
        return self._app_instances[interface]

    def _build(self, registration: DependencyRegistration):
        provider = registration.provider
        if inspect.isclass(provider):
            return provider(*registration.args, **registration.kwargs)
        if callable(provider):
            return provider(*registration.args, **registration.kwargs)
        return provider
