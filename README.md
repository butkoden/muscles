# Muscles Core

Muscles is an experimental framework core. The core package contains the
application lifecycle, configuration, shared schema objects, routing tree and
strategy interface. HTTP, ASGI and CLI packages reuse these primitives instead
of implementing their own framework model.

## Recommended Application Shape (Canonical Path)

Most projects use this lifecycle:

1. `App` class receives a runtime object (`runtime.strategy`, `runtime.routes`, `runtime.rest_api`).
2. `Context` is created with `runtime.strategy`.
3. REST API object is created through `runtime.rest_api(...)`.
4. Endpoints are registered with `runtime.routes.init(...)` or `api.init(...)`.
5. Execution goes through `Context.execute(...)`.

```python
from muscles import ApplicationMeta, Configurator, Context
from muscles.wsgi import wsgi_app

class App(metaclass=ApplicationMeta):
    package_paths = []
    shutup = False
    config = Configurator(obj={})

    def __init__(self, runtime):
        self.runtime = runtime
        self.context = Context(runtime.strategy, params={})
        self.api = runtime.rest_api(prefix="/api/v1")
        register_pages(runtime.routes)
        register_api(self.api, runtime.routes)

    def __call__(self, environ, start_response):
        self.context.set_param("environ", environ)
        self.context.set_param("start_response", start_response)
        return self.context.execute()


wsgi_app(App(wsgi_runtime()))
```

This style keeps runtime-specific glue thin and leaves endpoint modules with the
behavior and OpenAPI metadata.

## Packages

- `muscles` - core classes, schemas, routing and application metaclass.
- `muscles-wsgi` - WSGI runtime, pages, REST API and Swagger UI.
- `muscles-asgi` - ASGI runtime with the same routing and REST API model.
- `muscles-cli` - console command strategy built on the same route/group idea.
- `muscles-jsonrpc` - JSON-RPC projection for core actions.
- `muscles-sse` - Server-Sent Events projection for streaming actions.
- `muscles-mcp` - Model Context Protocol projection for AI tools.
- `muscles-sql` - SQL persistence helpers, named connections and diagnostics.
- `muscles-otel` - OpenTelemetry lifecycle instrumentation.
- `muscles-documents` - document loading, parsing, chunking and sync actions.
- `muscles-ai` - read-only AI/RAG actions and runtime contracts.
- `muscles-benchmarks` - benchmark and regression suite for the ecosystem.
- `muscular-example` - layered learning examples for Muscles applications.

## Repository Map

Core and runtimes:

- [`muscles`](https://github.com/butkoden/muscles) - framework core and canonical documentation.
- [`muscles-asgi`](https://github.com/butkoden/muscles-asgi) - ASGI HTTP/API runtime.
- [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) - WSGI HTTP/API runtime.
- [`muscles-cli`](https://github.com/butkoden/muscles-cli) - CLI runtime, project scaffolding and inspection commands.

Protocol projections:

- [`muscles-jsonrpc`](https://github.com/butkoden/muscles-jsonrpc) - JSON-RPC 2.0 projection over actions.
- [`muscles-sse`](https://github.com/butkoden/muscles-sse) - SSE delivery for `StreamResult` action output.
- [`muscles-mcp`](https://github.com/butkoden/muscles-mcp) - MCP tools/resources generated from Muscles contracts.

Framework extensions:

- [`muscles-sql`](https://github.com/butkoden/muscles-sql) - SQL layer for models, repositories, transactions and named SQL connections.
- [`muscles-otel`](https://github.com/butkoden/muscles-otel) - optional OpenTelemetry instrumentation for lifecycle and action execution.
- [`muscles-documents`](https://github.com/butkoden/muscles-documents) - document source ingestion, parsing, chunking and sync planning.
- [`muscles-ai`](https://github.com/butkoden/muscles-ai) - AI/RAG actions that can use document and data integrations.

Support repositories:

- [`muscles-benchmarks`](https://github.com/butkoden/muscles-benchmarks) - golden-path benchmarks and regression checks.
- [`muscular-example`](https://github.com/butkoden/muscular-example) - layered example application.
- [`muscles-landing`](https://github.com/butkoden/muscles-landing) - product site/application built on Muscles.
- [`muscular-asgi`](https://github.com/butkoden/muscular-asgi) - deprecated ASGI compatibility package.

## Installation

Muscles ecosystem currently uses GitHub source installs as the canonical method.
PyPI publishing is a target state, not yet the default distribution channel.

Installation matrix:

- core only: `pip install git+https://github.com/butkoden/muscles.git`
- ASGI runtime: `pip install git+https://github.com/butkoden/muscles-asgi.git`
- WSGI runtime: `pip install git+https://github.com/butkoden/muscles-wsgi.git`
- CLI tooling: `pip install git+https://github.com/butkoden/muscles-cli.git`
- JSON-RPC projection: `pip install git+https://github.com/butkoden/muscles-jsonrpc.git`
- SSE projection: `pip install git+https://github.com/butkoden/muscles-sse.git`
- MCP projection: `pip install git+https://github.com/butkoden/muscles-mcp.git`
- SQL extension: `pip install git+https://github.com/butkoden/muscles-sql.git`
- OTel extension: `pip install git+https://github.com/butkoden/muscles-otel.git`
- documents extension: `pip install git+https://github.com/butkoden/muscles-documents.git`
- AI extension: `pip install git+https://github.com/butkoden/muscles-ai.git`
- full/dev (source checkouts): clone all repositories and use `PYTHONPATH` with sibling `src` paths.

More detail: [docs/installation.md](docs/installation.md).
Repository ownership map: [docs/repositories.md](docs/repositories.md).

Core documentation:

- English: [docs/doc.md](docs/doc.md)
- Russian: [docs/doc.ru.md](docs/doc.ru.md)

## Naming

Use `Muscles` as the public framework name. Keep `muscles` for the Python
package/import name and `muscles-*` for official package identifiers.

More detail: [docs/naming.md](docs/naming.md).

## Positioning

Muscles is a framework for a **single application model** that can be projected
into multiple runtimes (WSGI, ASGI, CLI). It is not optimized for the shortest
"one endpoint in five minutes" path. It is optimized for consistency: the same
schemas, routing tree, lifecycle hooks and rules metadata stay reusable across
transports.

### When To Use Muscles

- you need Web/API/CLI to share one domain model and metadata;
- you want routing, schemas and rules to be declared once and reused;
- you want AI-assisted changes to follow a stable project structure.

### When Not To Use Muscles

- you only need a tiny HTTP service with no shared model beyond one runtime;
- your team prefers runtime-specific framework patterns per interface;
- you need mature batteries-included admin/ORM stack out of the box.

### FastAPI Relation

FastAPI is a strong choice for API-first delivery speed. Muscles targets a
different trade-off: one reusable model for API, pages and CLI workflows. These
tools can coexist in a portfolio; Muscles should not claim production maturity
or performance superiority without benchmark evidence.

More detail: [docs/positioning.md](docs/positioning.md).
Golden tutorial reference (planned): [Issue #16](https://github.com/butkoden/muscles/issues/16).

## Golden Path Structure

Use the official Muscles project structure as the default style for people and
AI assistants:

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

More detail: [docs/golden-path.md](docs/golden-path.md).
Tutorial: [docs/golden-tutorial.md](docs/golden-tutorial.md).

## Application Shape

An application is usually a class with `ApplicationMeta`, a `Configurator` and a
`Context` bound to a strategy:

```python
from muscles import ApplicationMeta, Configurator, Context
from muscles.wsgi import WsgiStrategy


class App(metaclass=ApplicationMeta):
    config = Configurator(obj={"main": {"DEBUG": True}})
    context = Context(WsgiStrategy, params={})

    def run(self, *args):
        return self.context.execute(*args, shutup=True)
```

`Context` owns lifecycle hooks and strategy execution. Keep it instance-local:
lists of hooks and params must not be shared between app instances.

## Routing

The core routing tree lives in `muscles.core.schema.itinerary`. It is used as a
generic structure for:

- page routes;
- REST API controllers/actions;
- CLI groups and commands;
- URL building and reverse lookup.

The current implementation indexes routes by `(path, method)` and keeps a match
cache. Static routes are checked before dynamic routes, so common paths avoid
walking the whole tree. Duplicate route registration is idempotent by route
name, which keeps repeated imports from making routing slower.

More detail: [docs/architecture.md](docs/architecture.md).

Backend primitives such as route groups, guards, middleware, exception mapping,
Bearer JWT auth, CORS and response helpers are documented in
[docs/backend-framework.md](docs/backend-framework.md).

`BackendPipeline` is the shared execution contract for runtime adapters. It
handles typed handler arguments, dependency resolution, guards, route-level
security and middleware, while ASGI/WSGI keep protocol parsing and response
serialization. `DependencyContainer` adds explicit `app`, `request` and
`transient` scopes for integrations that need more structure than legacy global
dependency registration.

## Schemas And OpenAPI

Schema classes (`Model`, `Collection`, `Column`, `String`, `Key`, request and
response bodies) describe data once and can be reused by runtime strategies. The
WSGI and ASGI packages read these structures to build OpenAPI automatically.

More detail: [docs/schema.md](docs/schema.md).

## Rules

Decorators such as `@rules` are intended to attach access control and metadata
to the same objects that routing uses. The important design rule is that a route,
API action or command should carry its permissions and properties together with
its schema, so every strategy can enforce or expose them consistently.

Practical examples: [docs/value-objects-rules.md](docs/value-objects-rules.md).

## Actions And Protocol Projections

Actions are first-class application contracts in core. Declare an action once
on a Muscles application instance, then let HTTP, CLI, MCP, JSON-RPC, SSE or
other protocol projections call it through the same dispatcher:

```python
from muscles import ApplicationMeta, Context, ActionDispatcher


class BookingApp(metaclass=ApplicationMeta):
    context = Context(MyStrategy, transport="app", params={})


app = BookingApp()


@app.action(
    name="bookings.create",
    description="Create a booking request",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "guest_count": {"type": "integer"},
        },
        "required": ["title"],
    },
    rules=["bookings.public_create"],
    transports=["http", "cli", "mcp"],
)
def create_booking(payload, context):
    return {"title": payload["title"], "transport": context.transport}


result = ActionDispatcher(app).execute(
    "bookings.create",
    {"title": "Discovery call"},
    transport="mcp",
)
```

`inspect_application(app)` is the source of truth for discovery. Protocol
packages should build tools, methods, routes or stream metadata from this
contract and send execution back to `ActionDispatcher`. They should not keep a
second validation, permissions or business model.

The action registry is application-scoped. New protocol projections should avoid
mutable module-level registries as their source of truth, because those leak
state between app instances and tests.

### Stream Results

English:

Streaming actions return `StreamResult(source=...)` with business
`StreamEvent(type="progress" | "log" | "result" | "error", data=...)` items.
The core contract is protocol-neutral: SSE heartbeat, MCP envelopes, JSON-RPC
notifications and CLI progress lines are transport projections over the same
events. Transports should preserve backpressure with bounded delivery and call
`close()` on disconnect when the source supports it. Long-blocking sources must
cooperate by unblocking the active `next()` call after `close()`.

Русский:

Streaming actions возвращают `StreamResult(source=...)` с business events
`StreamEvent(type="progress" | "log" | "result" | "error", data=...)`.
Core contract не зависит от протокола: SSE heartbeat, MCP envelopes,
JSON-RPC notifications и CLI progress lines являются transport-проекциями одних
и тех же событий. Transport должен сохранять backpressure через bounded delivery
и вызывать `close()` при disconnect, если source это поддерживает. Долгие
blocking sources должны быть cooperative: `close()` должен разблокировать
активный `next()`.

User docs:

- English: [docs/action-contract.en.md](docs/action-contract.en.md)
- Русский: [docs/action-contract.ru.md](docs/action-contract.ru.md)

## AI Workflow

Official AI-oriented instructions:

- [docs/ai/AGENTS.md](docs/ai/AGENTS.md)
- [docs/ai/cursor-rules.md](docs/ai/cursor-rules.md)
- [docs/ai/copilot-instructions.md](docs/ai/copilot-instructions.md)

## Production Deploy

Umbrella guide: [docs/production-deploy.md](docs/production-deploy.md).

## Benchmarks

Benchmark docs: [docs/benchmarks.md](docs/benchmarks.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Development

Run tests from each repository with its local `src` on `PYTHONPATH`:

```bash
PYTHONPATH=src python -m pytest -q
```

When testing an integration app that uses all packages from sibling checkouts:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-asgi/src:../muscles-cli/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-mcp/src:../muscles-sql/src:../muscles-otel/src:../muscles-documents/src:../muscles-ai/src python -m pytest -q
```
