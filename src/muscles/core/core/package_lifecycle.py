from __future__ import annotations

import inspect
from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Any, Mapping

from .actions import ActionContract, register_action
from .container import DependencyContainer
from .registry import get_application_registry


SENSITIVE_KEY_PARTS = (
    "secret",
    "token",
    "password",
    "credential",
    "authorization",
    "api_key",
    "private_key",
)


class TelemetryProvider:
    """Neutral telemetry surface used by core package lifecycle."""

    def span(self, name: str, **attributes: Any) -> Any:
        return nullcontext()


class NoopTelemetry(TelemetryProvider):
    pass


@dataclass(frozen=True)
class PackageService:
    interface: type
    provider: Any
    scope: str = DependencyContainer.APP
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)


class MusclesPackage:
    """Base contract for framework packages installed through Muscles core."""

    namespace: str = ""

    def build_runtime(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def services(self, *args: Any, **kwargs: Any) -> Any:
        return []

    def actions(self, *args: Any, **kwargs: Any) -> Any:
        return []

    def inspection_provider(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def doctor_provider(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def generator_providers(self, *args: Any, **kwargs: Any) -> Any:
        return []


def install_package(app, config: Any, package: Any):
    namespace = package_namespace(package)
    package_config = resolve_package_config(app, package, config)
    container = ensure_container(app)
    registry = get_application_registry(app)
    telemetry = resolve_telemetry(app)
    attributes = package_attributes(package)

    with telemetry.span("muscles.package.install", **attributes):
        registry.add_package(
            namespace,
            {
                "namespace": namespace,
                "name": package.__class__.__name__,
                "config_keys": sorted(package_config.keys()),
            },
        )

        with telemetry.span("muscles.package.runtime.build", **attributes):
            runtime = call_optional_package_hook(
                package,
                "build_runtime",
                default=None,
                ordered_names=("app", "config"),
                values={"app": app, "config": package_config},
            )

        with telemetry.span("muscles.package.services.register", **attributes):
            services = call_optional_package_hook(
                package,
                "services",
                default=[],
                ordered_names=("app", "runtime", "config"),
                values={"app": app, "runtime": runtime, "config": package_config},
            )
            register_services(container, services)

        with telemetry.span("muscles.package.actions.register", **attributes):
            actions = call_optional_package_hook(
                package,
                "actions",
                default=[],
                ordered_names=("app", "runtime", "config"),
                values={"app": app, "runtime": runtime, "config": package_config},
            )
            register_actions(app, actions)

        with telemetry.span("muscles.package.inspect.register", **attributes):
            provider = call_optional_package_hook(
                package,
                "inspection_provider",
                default=None,
                ordered_names=("app", "runtime", "config"),
                values={"app": app, "runtime": runtime, "config": package_config},
            )
            if provider is not None:
                registry.add_inspection_provider(namespace, provider)

        with telemetry.span("muscles.package.doctor.register", **attributes):
            provider = call_optional_package_hook(
                package,
                "doctor_provider",
                default=None,
                ordered_names=("app", "runtime", "config"),
                values={"app": app, "runtime": runtime, "config": package_config},
            )
            if provider is not None:
                registry.add_doctor_provider(namespace, provider)

        with telemetry.span("muscles.package.generators.register", **attributes):
            providers = call_optional_package_hook(
                package,
                "generator_providers",
                default=[],
                ordered_names=("app", "runtime", "config"),
                values={"app": app, "runtime": runtime, "config": package_config},
            )
            for provider in providers or []:
                registry.add_generator_provider(provider)

    return runtime


def call_optional_package_hook(
    package: Any,
    hook_name: str,
    *,
    default: Any,
    ordered_names: tuple[str, ...],
    values: dict[str, Any],
):
    hook = getattr(package, hook_name, None)
    if hook is None:
        return default
    if not callable(hook):
        raise TypeError(f"Package hook `{hook_name}` must be callable")
    return call_package_hook(hook, ordered_names=ordered_names, values=values)


def call_package_hook(hook, *, ordered_names: tuple[str, ...], values: dict[str, Any]):
    signature = inspect.signature(hook)
    ordered_values = [values[name] for name in ordered_names if name in values]
    consumed: set[str] = set()
    positional_index = 0
    args = []
    kwargs: dict[str, Any] = {}

    for parameter in signature.parameters.values():
        if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            args.extend(ordered_values[positional_index:])
            positional_index = len(ordered_values)
            continue
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            for name in ordered_names:
                if name in values and name not in consumed:
                    kwargs[name] = values[name]
            continue
        if parameter.kind == inspect.Parameter.KEYWORD_ONLY:
            if parameter.name in values:
                kwargs[parameter.name] = values[parameter.name]
                consumed.add(parameter.name)
            continue
        if parameter.name in values:
            args.append(values[parameter.name])
            consumed.add(parameter.name)
            continue
        if positional_index < len(ordered_values):
            args.append(ordered_values[positional_index])
            positional_index += 1
            continue
        if parameter.default is inspect.Parameter.empty:
            raise TypeError(f"Cannot resolve package hook parameter `{parameter.name}` for {hook}")

    return hook(*args, **kwargs)


def register_services(container: DependencyContainer, services: Any) -> None:
    for item in normalize_service_declarations(services):
        container.register(item.interface, item.provider, *item.args, scope=item.scope, **item.kwargs)


def register_actions(app, actions: Any) -> None:
    registry = get_application_registry(app)
    for item in list(actions or []):
        if isinstance(item, ActionContract):
            registry.add_action(item)
            continue
        if isinstance(item, Mapping):
            register_action(app, **dict(item))
            continue
        raise TypeError("Package actions must be ActionContract or mapping declarations")


def normalize_service_declarations(services: Any) -> list[PackageService]:
    if services is None:
        return []
    if isinstance(services, Mapping):
        return [PackageService(interface=interface, provider=provider) for interface, provider in services.items()]
    normalized: list[PackageService] = []
    for item in list(services or []):
        if isinstance(item, PackageService):
            normalized.append(item)
            continue
        if isinstance(item, Mapping):
            normalized.append(
                PackageService(
                    interface=item["interface"],
                    provider=item["provider"],
                    scope=item.get("scope", DependencyContainer.APP),
                    args=tuple(item.get("args", ())),
                    kwargs=dict(item.get("kwargs", {})),
                )
            )
            continue
        raise TypeError("Package services must be PackageService, mapping, or interface/provider mapping")
    return normalized


def ensure_container(app) -> DependencyContainer:
    container = getattr(app, "container", None)
    if container is None:
        container = DependencyContainer()
        setattr(app, "container", container)
    return container


def resolve_telemetry(app=None) -> TelemetryProvider:
    if app is None:
        return NoopTelemetry()

    for attribute in ("telemetry", "telemetry_provider"):
        provider = getattr(app, attribute, None)
        if provider is not None and hasattr(provider, "span"):
            return provider

    container = getattr(app, "container", None)
    if container is not None:
        try:
            provider = container.resolve(TelemetryProvider)
            if provider is not None and hasattr(provider, "span"):
                return provider
        except Exception:
            pass

    return NoopTelemetry()


def doctor_application(app=None) -> dict[str, Any]:
    registry = get_application_registry(app, create=False) if app is not None else None
    if registry is None:
        return {"status": "ok", "packages": {}}

    telemetry = resolve_telemetry(app)
    packages: dict[str, Any] = {}
    overall = "ok"
    for namespace, provider in sorted(registry.doctor_providers.items()):
        with telemetry.span(
            "muscles.package.doctor.run",
            **{
                "muscles.package.namespace": namespace,
                "muscles.package.name": registry.packages.get(namespace, {}).get("name"),
            },
        ):
            payload = provider() if callable(provider) else provider
        safe_payload = sanitize_payload(payload or {})
        packages[namespace] = safe_payload
        status = str(safe_payload.get("status", "ok")).lower() if isinstance(safe_payload, dict) else "ok"
        if status in {"error", "failed", "fail"}:
            overall = "error"
        elif status in {"warning", "warn"} and overall == "ok":
            overall = "warning"
    return {"status": overall, "packages": packages}


def collect_package_capabilities(app) -> dict[str, Any]:
    registry = get_application_registry(app, create=False)
    if registry is None:
        return {}
    capabilities: dict[str, Any] = {}
    for namespace, provider in sorted(registry.inspection_providers.items()):
        payload = provider() if callable(provider) else provider
        capabilities[namespace] = sanitize_payload(payload or {})
    return capabilities


def collect_packages(app) -> list[dict[str, Any]]:
    registry = get_application_registry(app, create=False)
    if registry is None:
        return []
    packages = []
    for namespace in sorted(registry.packages):
        item = dict(registry.packages[namespace])
        packages.append({"namespace": item.get("namespace", namespace), "name": item.get("name")})
    return packages


def resolve_package_config(app, package: MusclesPackage, config: Any) -> dict[str, Any]:
    if config is not None:
        return normalize_config(config)

    namespace = package_namespace(package)
    app_config = getattr(app, "config", None)
    raw = getattr(app_config, "_object", None)
    if isinstance(raw, Mapping):
        package_config = raw.get("packages", {}).get(namespace)
        if package_config is None:
            package_config = raw.get(namespace, {})
        return normalize_config(package_config)
    return {}


def normalize_config(config: Any) -> dict[str, Any]:
    if config is None:
        return {}
    if isinstance(config, Mapping):
        return dict(config)
    if hasattr(config, "_object"):
        return normalize_config(getattr(config, "_object"))
    if hasattr(config, "__dict__"):
        return dict(getattr(config, "__dict__") or {})
    try:
        return dict(config)
    except Exception:
        return {}


def package_namespace(package: MusclesPackage) -> str:
    namespace = getattr(package, "namespace", None)
    if not namespace:
        raise ValueError("Muscles package must define a non-empty namespace")
    return str(namespace)


def package_attributes(package: MusclesPackage) -> dict[str, Any]:
    return {
        "muscles.package.namespace": package_namespace(package),
        "muscles.package.name": package.__class__.__name__,
    }


def sanitize_payload(value: Any, *, key: str | None = None) -> Any:
    if key is not None and is_sensitive_key(key):
        return "<redacted>"
    if isinstance(value, Mapping):
        return {str(item_key): sanitize_payload(item_value, key=str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_payload(item) for item in value]
    return value


def is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)
