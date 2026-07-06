from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from muscles.core import (
    ActionDispatcher,
    Configurator,
    DependencyContainer,
    GenerationRequest,
    MusclesPackage,
    NoopTelemetry,
    PackageService,
    TelemetryProvider,
    doctor_application,
    get_application_registry,
    inspect_application,
    install_package,
    resolve_telemetry,
)


class DemoRuntime:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint


class DemoGenerator:
    name = "demo"

    def supports(self, generator_type: str) -> bool:
        return generator_type == "demo"

    def generate(self, project_root: Path, request: GenerationRequest) -> list[str]:
        return [str(project_root / f"{request.name}.demo")]


class DemoPackage(MusclesPackage):
    namespace = "demo"

    def build_runtime(self, app, config) -> Any:
        return DemoRuntime(endpoint=config["endpoint"])

    def services(self, app, runtime, config) -> Any:
        return [PackageService(DemoRuntime, runtime)]

    def actions(self, app, runtime, config) -> Any:
        return [
            {
                "name": "demo.echo",
                "description": "Echo through demo runtime",
                "input_schema": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                "transports": ["cli", "mcp"],
                "handler": self.echo,
            }
        ]

    def echo(self, payload, context):
        runtime = context.application.container.resolve(DemoRuntime)
        return {"text": payload["text"], "endpoint": runtime.endpoint, "transport": context.transport}

    def inspection_provider(self, app, runtime, config) -> Any:
        return lambda: {
            "features": ["echo"],
            "config_keys": sorted(config.keys()),
            "api_token": "must-not-leak",
        }

    def doctor_provider(self, app, runtime, config) -> Any:
        return lambda: {
            "status": "ok",
            "checks": [{"name": "demo.endpoint", "status": "ok"}],
            "password": "must-not-leak",
        }

    def generator_providers(self, app, runtime, config) -> Any:
        return [DemoGenerator()]


class RecordingTelemetry(TelemetryProvider):
    def __init__(self):
        self.spans: list[tuple[str, dict]] = []

    @contextmanager
    def span(self, name: str, **attributes) -> Any:
        self.spans.append((name, dict(attributes)))
        yield


class DemoApp:
    container: DependencyContainer
    config = Configurator(
        obj={
            "main": {"ENV": "development"},
            "packages": {
                "demo": {
                    "endpoint": "https://demo.local",
                    "api_token": "secret-value",
                }
            }
        }
    )


class KeywordConfigPackage(MusclesPackage):
    namespace = "keyword"

    def build_runtime(self, app, config) -> Any:
        return DemoRuntime(endpoint=config["endpoint"])

    def services(self, app, runtime) -> Any:
        return {DemoRuntime: runtime}

    def actions(self, app, runtime, *, config) -> Any:
        return []


def test_install_package_registers_runtime_services_actions_inspection_doctor_and_generators():
    app = DemoApp()

    runtime = install_package(app, None, DemoPackage())

    assert isinstance(runtime, DemoRuntime)
    assert app.container.resolve(DemoRuntime) is runtime

    result = ActionDispatcher(app).execute("demo.echo", {"text": "hello"}, transport="cli")
    assert result.value == {
        "text": "hello",
        "endpoint": "https://demo.local",
        "transport": "cli",
    }

    registry = get_application_registry(app)
    assert registry.packages["demo"]["namespace"] == "demo"
    assert "runtime" not in registry.packages["demo"]
    assert registry.generator_registry.resolve("demo").generate(Path("/tmp"), GenerationRequest("demo", "sample")) == [
        "/tmp/sample.demo"
    ]

    contract = inspect_application(app)
    assert contract["packages"] == [{"namespace": "demo", "name": "DemoPackage"}]
    assert contract["capabilities"]["demo"]["features"] == ["echo"]
    assert contract["capabilities"]["demo"]["config_keys"] == ["api_token", "endpoint"]
    assert contract["capabilities"]["demo"]["api_token"] == "<redacted>"

    doctor = doctor_application(app)
    assert doctor["status"] == "ok"
    assert doctor["packages"]["demo"]["checks"] == [{"name": "demo.endpoint", "status": "ok"}]
    assert doctor["packages"]["demo"]["password"] == "<redacted>"


def test_install_package_uses_neutral_telemetry_provider_without_leaking_config_values():
    app = DemoApp()
    telemetry = RecordingTelemetry()
    app.container = DependencyContainer()
    app.container.register(TelemetryProvider, telemetry)

    install_package(app, None, DemoPackage())
    doctor_application(app)

    span_names = [name for name, _attrs in telemetry.spans]
    assert span_names == [
        "muscles.package.install",
        "muscles.package.runtime.build",
        "muscles.package.services.register",
        "muscles.package.actions.register",
        "muscles.package.inspect.register",
        "muscles.package.doctor.register",
        "muscles.package.generators.register",
        "muscles.package.doctor.run",
    ]
    assert all(attrs["muscles.package.namespace"] == "demo" for _name, attrs in telemetry.spans)
    assert all("secret-value" not in str(attrs) for _name, attrs in telemetry.spans)


def test_resolve_telemetry_defaults_to_noop_provider():
    assert isinstance(resolve_telemetry(object()), NoopTelemetry)


def test_install_package_supports_keyword_only_config_hooks():
    app = DemoApp()
    runtime = install_package(app, {"endpoint": "keyword"}, KeywordConfigPackage())

    assert app.container.resolve(DemoRuntime) is runtime
