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

## Naming

Use `Muscles` as the public framework name. Keep `muscles` for the Python
package/import name and `muscles-*` for official package identifiers.

More detail: [docs/naming.md](docs/naming.md).

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

## Development

Run tests from each repository with its local `src` on `PYTHONPATH`:

```bash
PYTHONPATH=src python -m pytest -q
```

When testing an integration app that uses all packages from sibling checkouts:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-asgi/src:../muscles-cli/src python -m pytest -q
```
