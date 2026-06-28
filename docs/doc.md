# Muscles Core Documentation

Language: English  
Russian version: [doc.ru.md](doc.ru.md)

This is the canonical entry point for Muscles core documentation. Topic-specific
documents are still kept as deeper references, but new core behavior should be
reflected here and in the Russian version.

## What Muscles Core Provides

`muscles` is the shared core package for the Muscles ecosystem. It contains:

- application lifecycle primitives;
- configuration and runtime mode helpers;
- dependency injection;
- context and strategy contracts;
- schemas, fields, value objects and OpenAPI metadata objects;
- the shared routing tree (`Itinerary`);
- response normalization helpers;
- backend framework primitives used by ASGI and WSGI runtimes.

Runtime packages such as `muscles-asgi`, `muscles-wsgi` and `muscles-cli`
project these core contracts into concrete protocols.

## Ecosystem Extensions

Core deliberately keeps protocol-neutral contracts. Runtime and integration
repositories extend those contracts:

- [`muscles-asgi`](https://github.com/butkoden/muscles-asgi) - ASGI runtime,
  async request/response handling, REST API projection, OpenAPI/Swagger UI,
  ASGI `TestClient`, file uploads and CORS preflight over core routing.
- [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) - WSGI runtime,
  request/response handling, page/template support, static files, REST API
  projection, OpenAPI/Swagger UI, uploads and CORS preflight over core routing.
- [`muscles-cli`](https://github.com/butkoden/muscles-cli) - CLI projection of
  the same application model, command/group routing and project scaffolding.
- [`muscles-sql`](https://github.com/butkoden/muscles-sql) - SQL-oriented
  persistence extension for applications that need database integration.
- [`muscles-jsonrpc`](https://github.com/butkoden/muscles-jsonrpc) - JSON-RPC
  protocol projection for core actions and application contracts.
- [`muscles-sse`](https://github.com/butkoden/muscles-sse) - Server-Sent Events
  projection for streaming action results.
- [`muscles-otel`](https://github.com/butkoden/muscles-otel) - observability
  extension for OpenTelemetry-style instrumentation.
- [`muscles-mcp`](https://github.com/butkoden/muscles-mcp) - MCP projection for
  exposing core application actions as tools.
- [`muscular-example`](https://github.com/butkoden/muscular-example) - example
  application that demonstrates how ecosystem packages fit together.

When adding a core feature, document the protocol-neutral contract here and add
runtime-specific examples in the extension repository that executes it.

## Installation

Current canonical installation uses GitHub source installs:

```bash
pip install git+https://github.com/butkoden/muscles.git
```

Use runtime packages when you need a web/API transport:

```bash
pip install git+https://github.com/butkoden/muscles-asgi.git
pip install git+https://github.com/butkoden/muscles-wsgi.git
```

More detail: [installation.md](installation.md).

## Application Shape

A Muscles application is usually a class with `ApplicationMeta`, `Configurator`
and `Context`:

```python
from muscles import ApplicationMeta, Configurator, Context


class App(metaclass=ApplicationMeta):
    config = Configurator(obj={"main": {"DEBUG": True}})
    context = Context(MyStrategy, params={})

    def run(self, *args):
        return self.context.execute(*args, shutup=True)
```

`Context` owns runtime execution and lifecycle hooks. Strategy packages decide
how to translate external input into this shared application contract.

More detail: [architecture.md](architecture.md), [context.md](context.md),
[instance.md](instance.md).

## Golden Path Project Structure

Recommended application layout:

```text
app/
  application.py
  config.py
  domain/
  schemas/
  web/
  api/
  cli/
  rules/
  templates/
  static/
tests/
```

Keep HTTP, CLI and other entry handlers thin. Put shared business behavior in
domain services and value objects.

More detail: [golden-path.md](golden-path.md),
[golden-tutorial.md](golden-tutorial.md).

## Routing And API Modules

`Itinerary` is the core route tree. It registers routes, matches request paths,
builds URLs and stores route metadata. Runtime packages reuse this structure for
HTTP routes, REST controllers, static routes and CLI command trees.

Route groups add a shared prefix and metadata:

```python
from muscles import Itinerary, BearerAuthSecurity

api = Itinerary(name="api")
auth = BearerAuthSecurity()

documents = api.group(
    "/api/documents",
    tags=["Documents"],
    security=[auth],
    response={401: "Unauthorized"},
)


@documents.init("/{id}", method="get", summary="Show document")
def show_document(request, id):
    return {"id": id}
```

ASGI and WSGI OpenAPI builders use group metadata for tags, security and common
responses.

More detail: [backend-framework.md](backend-framework.md).

## Middleware, Guards And CORS

`use()` registers middleware. Middleware receives `(request, call_next)` and
returns a response:

```python
def audit_middleware(request, call_next):
    response = call_next(request)
    return response


api.use(audit_middleware)
```

`guard()` registers a route guard by path pattern:

```python
def require_auth(request):
    if request.user.is_guest():
        return {"error": "unauthorized"}, 401


api.guard("/api/**", require_auth, except_=["/api/public/**"])
```

CORS is provided as shared middleware:

```python
from muscles import cors

api.use(cors(
    allow_origins=["https://app.example"],
    allow_credentials=True,
))
```

ASGI and WSGI runtimes use the same CORS middleware for normal responses and
`OPTIONS` preflight responses.

## Auth And Error Mapping

`BearerAuthSecurity` describes HTTP bearer auth for OpenAPI. `BearerJwtAuth`
adds a small HS256 JWT provider:

```python
from muscles import BearerJwtAuth

jwt_auth = BearerJwtAuth(secret=settings.jwt_secret, subject="sub")
token = jwt_auth.issue({"sub": "user-1"})
auth_result = jwt_auth.authenticate_header(f"Bearer Bearer {token}")
```

`authenticate_header()` accepts duplicate bearer prefixes for legacy
compatibility and returns `payload`, `token` and `user`. The returned user has
`uid` set from the configured subject claim.

Domain exceptions can be mapped to HTTP statuses:

```python
api.map_error(PermissionError, status=403)
api.map_error(ValueError, status=422)
```

ASGI and WSGI preserve mapped statuses when handlers raise mapped exceptions.

## Responses

Core response helpers are normalized by runtime packages:

```python
from muscles import BytesResponse, FileResponse, JsonResponse, NoContentResponse

return JsonResponse({"ok": True})
return NoContentResponse()
return BytesResponse(b"PNG", content_type="image/png")
return FileResponse("/tmp/report.pdf", as_attachment=True)
```

`None` becomes `204 No Content`, mappings become JSON, strings become HTML and
bytes become `application/octet-stream`.

## Schemas, Models And OpenAPI

Schema classes describe data once and can be reused by runtime projections:

```python
from muscles import Column, Key, Model, String


class Document(Model):
    id = Column(Key)
    title = Column(String, required=True)
```

Request bodies, response bodies and parameters are consumed by ASGI and WSGI
OpenAPI builders.

More detail: [schema.md](schema.md).

## Dependency Injection

Core DI is based on `Dependency`, `DependencyStorage` and `inject()`:

```python
from muscles import Dependency


class StoreInterface:
    pass


@Dependency.init(StoreInterface)
class Store(StoreInterface):
    pass
```

Runtime handler pipelines can resolve annotated dependencies from this core
container.

More detail: [dependency.md](dependency.md).

## Configuration And Runtime Mode

`Configurator` reads project configuration. Runtime mode helpers define
development, test and production behavior.

More detail: [configure.md](configure.md).

## Actions

Core actions are protocol-neutral contracts. They can be projected into HTTP,
CLI, MCP, JSON-RPC, SSE or other runtime layers through `ActionDispatcher`.

More detail:

- [action-contract.en.md](action-contract.en.md)
- [action-contract.ru.md](action-contract.ru.md)

## Testing Core From Source

From the core repository:

```bash
PYTHONPATH=src python3 -m pytest
```

When testing ecosystem packages from sibling checkouts:

```bash
PYTHONPATH=../muscles/src:src python3 -m pytest
```

## Deep References

- Ecosystem runtime docs:
  - [`muscles-asgi`](https://github.com/butkoden/muscles-asgi)
  - [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi)
  - [`muscles-cli`](https://github.com/butkoden/muscles-cli)
- [architecture.md](architecture.md)
- [backend-framework.md](backend-framework.md)
- [backend-framework.ru.md](backend-framework.ru.md)
- [benchmarks.md](benchmarks.md)
- [configure.md](configure.md)
- [context.md](context.md)
- [dependency.md](dependency.md)
- [golden-path.md](golden-path.md)
- [golden-tutorial.md](golden-tutorial.md)
- [installation.md](installation.md)
- [naming.md](naming.md)
- [positioning.md](positioning.md)
- [production-deploy.md](production-deploy.md)
- [roadmap-baseline.md](roadmap-baseline.md)
- [schema.md](schema.md)
- [value-objects-rules.md](value-objects-rules.md)
- [watchdog.md](watchdog.md)
