# Muscles Core Documentation

Language: English  
Russian version: [doc.ru.md](doc.ru.md)

This is the canonical entry point for Muscles core documentation. Topic-specific
documents are still kept as deeper references, but new core behavior should be
reflected here and in the Russian version.

Public symbols exported by `muscles` / `muscles.core` are documented in
[public-api.md](public-api.md).

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
Extension packages such as `muscles-ai`, `muscles-documents`, `muscles-sql`
and `muscles-otel` add reusable framework capabilities without changing the
core application model.

## Ecosystem Repository Reference

Core deliberately keeps protocol-neutral contracts. Runtime, protocol and
integration repositories extend those contracts. Use this table as a quick
navigation reference when deciding where a behavior should live.

### Runtime And Protocol Extensions

[`muscles-asgi`](https://github.com/butkoden/muscles-asgi) provides the ASGI
runtime over core routing and schemas. Use it for async HTTP apps, REST APIs,
OpenAPI/Swagger UI, typed handler invocation, file uploads, CORS preflight and
the ASGI `TestClient`.

[`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) provides the WSGI
runtime over core routing and schemas. Use it for classic WSGI HTTP apps,
pages/templates, static files, REST APIs, OpenAPI/Swagger UI, uploads and CORS
preflight.

[`muscles-cli`](https://github.com/butkoden/muscles-cli) projects the same
application model into CLI commands. Use it for command/group routing, local
developer tools and project scaffolding based on the golden path.

[`muscles-jsonrpc`](https://github.com/butkoden/muscles-jsonrpc) exposes core
actions and application contracts through JSON-RPC methods.

[`muscles-sse`](https://github.com/butkoden/muscles-sse) delivers streaming
action results through Server-Sent Events.

[`muscles-mcp`](https://github.com/butkoden/muscles-mcp) exposes application
actions as MCP tools.

### Data, Observability And Integration Extensions

[`muscles-sql`](https://github.com/butkoden/muscles-sql) is the SQL persistence
extension. Use it for database integration and persistence patterns that should
stay outside protocol runtimes.

[`muscles-otel`](https://github.com/butkoden/muscles-otel) is the observability
extension. Use it for OpenTelemetry-style instrumentation, traces and metrics
around core/runtime behavior.

[`muscles-documents`](https://github.com/butkoden/muscles-documents) is the
document ingestion extension. Use it for local/markdown/text document loading,
parsing, chunking and sync planning behind Muscles actions.

[`muscles-ai`](https://github.com/butkoden/muscles-ai) is the AI/RAG extension.
Use it for read-only question answering, retrieval and AI diagnostics over the
same action/dispatcher model used by protocol projections.

### Examples, Compatibility And Support Repositories

[`muscular-example`](https://github.com/butkoden/muscular-example) is an
example application showing how core, runtime and extension packages fit
together.

[`muscles-benchmarks`](https://github.com/butkoden/muscles-benchmarks) is the
benchmark workspace for measuring routing, DI and runtime performance changes.

[`muscles-landing`](https://github.com/butkoden/muscles-landing) contains the
public product and documentation site.

[`muscular-asgi`](https://github.com/butkoden/muscular-asgi) is the legacy ASGI
compatibility package, kept for historical checks while the ecosystem converges
on `muscles-asgi`.

When adding a core feature, document the protocol-neutral contract here and add
runtime-specific examples in the extension repository that executes it.
Detailed ownership map: [repositories.md](repositories.md).

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

Use extension packages when you need reusable framework capabilities:

```bash
pip install git+https://github.com/butkoden/muscles-documents.git
pip install git+https://github.com/butkoden/muscles-ai.git
pip install git+https://github.com/butkoden/muscles-sql.git
pip install git+https://github.com/butkoden/muscles-otel.git
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

Endpoint metadata for OpenAPI and transport behavior is attached directly in the
route decorators (`summary`, `description`, `tags`, `security`, `request`,
`response`, `parameters`).

```python
from muscles import Itinerary, JsonResponseBody, BearerAuthSecurity

api = Itinerary(name="api")
documents = api.group("/api/documents", tags=["Documents"], security=[BearerAuthSecurity()])


@documents.init(
    "/{id}",
    method="get",
    summary="Show document",
    description="Returns a document for the current user.",
    security=[BearerAuthSecurity()],
    response={200: JsonResponseBody(description="Document loaded")},
)
def show_document(request, id):
    return {"id": id}
```

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

Endpoint auth can override group auth:

```python
@api.init("/api/login", method="post", auth=False)
def login(request):
    return {"token": "issued-token"}
```

Use `auth=False` for public endpoints inside protected route groups. Use
`auth=[...]` to replace inherited security for one endpoint.

More detail: [backend-framework.md](backend-framework.md).

## Endpoint Key Rule (Important)

`routes.init(...)` uses both `route` and `key` together with `method`.

- You may use one shared `key` for all methods of the same path.
- You may also use distinct keys per method when operation names must differ.
- Route lookup selects from all route records attached to the matched terminal
  node, then filters by method and content type.

```python
# Shared key
@api.init("/api/documents", key="documents.collection", method="get", summary="List")
def list_documents(request):
    ...


@api.init("/api/documents", key="documents.collection", method="post", summary="Create")
def create_document(request):
    ...


# Distinct keys
@api.init("/api/documents", key="documents.list", method="get", summary="List")
def list_documents_v2(request):
    ...


@api.init("/api/documents", key="documents.create", method="post", summary="Create")
def create_document_v2(request):
    ...
```

Prefer `auth=False` for public endpoints and explicit security objects
(`BearerAuthSecurity`, `ApiKeyAuthSecurity`) for protected endpoints.

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

Prefer `auth=False` over a long `except_` list when a single endpoint such as
`/api/login` intentionally stays public.

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
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-mcp/src:../muscles-sql/src:../muscles-otel/src:../muscles-documents/src:../muscles-ai/src:src python3 -m pytest
```

## Deep References

- Ecosystem repository map:
  - [repositories.md](repositories.md)
- Ecosystem runtime and extension docs:
  - [`muscles-asgi`](https://github.com/butkoden/muscles-asgi)
  - [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi)
  - [`muscles-cli`](https://github.com/butkoden/muscles-cli)
  - [`muscles-jsonrpc`](https://github.com/butkoden/muscles-jsonrpc)
  - [`muscles-sse`](https://github.com/butkoden/muscles-sse)
  - [`muscles-mcp`](https://github.com/butkoden/muscles-mcp)
  - [`muscles-sql`](https://github.com/butkoden/muscles-sql)
  - [`muscles-otel`](https://github.com/butkoden/muscles-otel)
  - [`muscles-documents`](https://github.com/butkoden/muscles-documents)
  - [`muscles-ai`](https://github.com/butkoden/muscles-ai)
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
- [public-api.md](public-api.md)
- [production-deploy.md](production-deploy.md)
- [roadmap-baseline.md](roadmap-baseline.md)
- [schema.md](schema.md)
- [value-objects-rules.md](value-objects-rules.md)
- [watchdog.md](watchdog.md)
