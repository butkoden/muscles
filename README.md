# Muscles Core

Muscles is an experimental framework core. The core package contains the
application lifecycle, configuration, shared schema objects, routing tree and
strategy interface. HTTP, ASGI and CLI packages reuse these primitives instead
of implementing their own framework model.

## Packages

- `muscles` - core classes, schemas, routing and application metaclass.
- `muscles-wsgi` - WSGI runtime, pages, REST API and Swagger UI.
- `muscles-asgi` - ASGI runtime with the same routing and REST API model.
- `muscles-cli` - console command strategy built on the same route/group idea.

## Installation

Muscles ecosystem currently uses GitHub source installs as the canonical method.
PyPI publishing is a target state, not yet the default distribution channel.

Installation matrix:

- core only: `pip install git+https://github.com/butkoden/muscles.git`
- ASGI runtime: `pip install git+https://github.com/butkoden/muscles-asgi.git`
- WSGI runtime: `pip install git+https://github.com/butkoden/muscles-wsgi.git`
- CLI tooling: `pip install git+https://github.com/butkoden/muscles-cli.git`
- full/dev (source checkouts): clone all repositories and use `PYTHONPATH` with sibling `src` paths.

More detail: [docs/installation.md](docs/installation.md).

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
    context = Context(WsgiStrategy, {})

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
    context = Context(MyStrategy, {})


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
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-asgi/src:../muscles-cli/src python -m pytest -q
```
