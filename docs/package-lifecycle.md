# Framework Package Lifecycle

`muscles` exposes a neutral lifecycle for framework packages such as
`muscles-ai`, `muscles-documents`, `muscles-sql`, protocol projections and
future data/storage packages.

The goal is to keep package-specific code small while core performs the common
installation mechanics:

1. Resolve package config.
2. Build runtime state.
3. Register runtime services in the app `DependencyContainer`.
4. Register protocol-neutral actions.
5. Register inspection capabilities.
6. Register doctor checks.
7. Register generator providers.
8. Emit neutral telemetry spans.

## Public API

```python
from muscles import MusclesPackage, PackageService, install_package


class DocumentsPackage(MusclesPackage):
    namespace = "documents"

    def build_runtime(self, app, config):
        return DocumentsRuntime(config)

    def services(self, app, runtime):
        return [PackageService(DocumentsRuntime, runtime)]

    def actions(self, app, runtime, *, config):
        return [
            {
                "name": "documents.search",
                "transports": ["http", "cli", "mcp"],
                "handler": self.search,
            }
        ]

    def inspection_provider(self, app, runtime, config):
        return lambda: {"sources": runtime.source_names(), "config_keys": sorted(config.keys())}

    def doctor_provider(self, app, runtime, config):
        return lambda: {"status": "ok", "checks": runtime.checks()}


def init_package(app, config):
    return install_package(app, config, DocumentsPackage())
```

Compatibility exports are available from:

- `muscles`
- `muscles.core`
- `muscles.core.lifecycle`
- `muscles.lifecycle`

Packages do not have to subclass `MusclesPackage` when they follow the same
duck-typed contract. `namespace` and `build_runtime(...)` are required; missing
optional hooks are treated as safe defaults:

- `services` -> `[]`
- `actions` -> `[]`
- `inspection_provider` -> `None`
- `doctor_provider` -> `None`
- `generator_providers` -> `[]`

`inspect_application(app)["packages"]` reports the original package class name,
even when the package uses this partial contract.

## Runtime State Rule

`ApplicationRegistry` stores only metadata and providers:

- package name and namespace;
- action contracts;
- inspection providers;
- doctor providers;
- generator providers.

Runtime clients, DB connections, vector clients, LLM clients and other live
objects must live in `DependencyContainer` or package-owned lazy managers, not
inside `ApplicationRegistry`.

## Config Resolution

`install_package(app, config, package)` uses explicit `config` when provided.
When `config` is `None`, it reads app config from:

1. `app.config._object["packages"][package.namespace]`
2. `app.config._object[package.namespace]`
3. empty dict fallback

Config values are not emitted to telemetry. Inspection and doctor payloads are
sanitized recursively for sensitive keys such as `secret`, `token`, `password`,
`credential`, `authorization`, `api_key` and `private_key`.

## Inspection And Doctor

`inspect_application(app)` now includes:

```json
{
  "packages": [{"namespace": "documents", "name": "DocumentsPackage"}],
  "capabilities": {
    "documents": {
      "sources": ["repo"],
      "config_keys": ["sources", "chunk_size"]
    }
  }
}
```

Doctor checks are collected separately:

```python
from muscles import doctor_application

doctor = doctor_application(app)
```

Shape:

```json
{
  "status": "ok",
  "packages": {
    "documents": {
      "status": "ok",
      "checks": [{"name": "documents.repo", "status": "ok"}]
    }
  }
}
```

## Neutral Telemetry

Core does not import `muscles_otel`. Packages can provide telemetry through:

- `app.telemetry`
- `app.telemetry_provider`
- `app.container.register(TelemetryProvider, provider)`

If no provider exists, core uses `NoopTelemetry`.

Lifecycle spans:

- `muscles.package.install`
- `muscles.package.runtime.build`
- `muscles.package.services.register`
- `muscles.package.actions.register`
- `muscles.package.inspect.register`
- `muscles.package.doctor.register`
- `muscles.package.generators.register`
- `muscles.package.doctor.run`

Span attributes contain only safe metadata:

- `muscles.package.namespace`
- `muscles.package.name`

## Backward Compatibility

Legacy `init_package(app, config)` functions remain valid. New packages should
implement them as a thin wrapper over `install_package(...)`. Existing packages
that still perform manual registration are not broken by this lifecycle.
