# Framework Package Lifecycle

`muscles` exposes a neutral lifecycle for framework packages such as
`muscles-ai`, `muscles-documents`, `muscles-sql`, protocol projections and
future data/storage packages.

Use this API when a package needs to add framework capabilities to one Muscles
application: runtime services, protocol-neutral actions, inspection data,
doctor checks or code-generation providers. The package stays focused on its
own domain while core performs the shared installation mechanics:

1. Resolve package config.
2. Build runtime state.
3. Register runtime services in the app `DependencyContainer`.
4. Register protocol-neutral actions.
5. Register inspection capabilities.
6. Register doctor checks.
7. Register generator providers.
8. Emit neutral telemetry spans.

## Quick Mental Model

There are two different places involved in package installation:

- `DependencyContainer` stores live runtime objects: clients, pools, tracers,
  repositories and package managers.
- `ApplicationRegistry` stores the application contract: routes, actions,
  package metadata, inspection providers, doctor providers and generator
  providers.

That split is intentional. Runtime code resolves services from the container.
Developer tooling reads the registry through `inspect_application(app)`,
`doctor_application(app)` and generators. The registry should explain the app;
it should not become a service locator for live objects.

## When To Use A Package

Create a `MusclesPackage` when an integration must be installed consistently
across runtimes or inspected by tooling. Common examples:

- a storage package that registers repositories and health checks;
- an observability package that registers a neutral telemetry provider;
- a documents or AI package that registers actions for HTTP, CLI and MCP;
- a protocol package that reads existing actions and exposes them elsewhere.

Do not use a package lifecycle just to call one helper function. For simple
application-local wiring, regular Python code is clearer.

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

Applications install the package during app construction or bootstrap:

```python
from documents_package import DocumentsPackage
from muscles import doctor_application, inspect_application, install_package

app = App()
documents = install_package(
    app,
    {"sources": ["repo"], "chunk_size": 800},
    DocumentsPackage(),
)

contract = inspect_application(app)
doctor = doctor_application(app)
```

Compatibility exports are available from:

- `muscles`
- `muscles.core`
- `muscles.core.lifecycle`
- `muscles.lifecycle`

Packages do not have to subclass `MusclesPackage` when they follow the same
duck-typed contract. `namespace` is required; missing hooks are treated as safe
defaults:

- `build_runtime` -> `None`
- `services` -> `[]`
- `actions` -> `[]`
- `inspection_provider` -> `None`
- `doctor_provider` -> `None`
- `generator_providers` -> `[]`

`inspect_application(app)["packages"]` reports the original package class name,
even when the package uses this partial contract.

## Hook Roles

Each hook has one job:

| Hook | Purpose | Stored In |
| --- | --- | --- |
| `build_runtime(app, config)` | Build the package runtime object when the package needs one. | Returned from `install_package(...)`; `None` when omitted |
| `services(app, runtime, config)` | Register live services for app code to resolve. | `DependencyContainer` |
| `actions(app, runtime, config)` | Register protocol-neutral callable contracts. | `ApplicationRegistry.actions` |
| `inspection_provider(app, runtime, config)` | Expose safe capability data for tooling. | `ApplicationRegistry.inspection_providers` |
| `doctor_provider(app, runtime, config)` | Expose health/readiness checks. | `ApplicationRegistry.doctor_providers` |
| `generator_providers(app, runtime, config)` | Add code/document generation providers. | `ApplicationRegistry.generator_registry` |

All hooks may be omitted. A package without `build_runtime(...)` can still
register services, actions, inspection providers, doctor providers or generator
providers; those hooks receive `runtime=None`.

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

Application code should consume a package through the container or through the
runtime returned by `install_package(...)`:

```python
runtime = install_package(app, config, DocumentsPackage())
same_runtime = app.container.resolve(DocumentsRuntime)
```

Tooling should consume the same package through inspection and doctor data:

```python
from muscles import doctor_application, inspect_application

capabilities = inspect_application(app)["capabilities"]
health = doctor_application(app)
```

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
