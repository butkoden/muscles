# Architecture

Muscles is built around a small set of reusable primitives. A runtime strategy
decides how to receive input and return output, but the shape of the application
is shared.

Positioning summary: Muscles is aimed at a unified application model across
interfaces, not at shortest API-only bootstrap. See [positioning.md](positioning.md).
Default project structure is fixed in [golden-path.md](golden-path.md).

## Base Application

`ApplicationMeta` prepares application classes and helper methods. An app then
defines:

- `config` as a `Configurator`;
- `context` as a `Context(<Strategy>, params)`;
- `run()` as a small wrapper around `context.execute()`;
- imports or package discovery in `__init__()` when routes/controllers must be
  registered.

`Context` is deliberately instance-local. Hooks registered with
`before_start()` and `after_start()` belong to the concrete app instance, not to
the class globally.

## Strategies

A strategy implements the runtime contract. Examples:

- WSGI: translates `environ` into a framework request and returns WSGI output;
- ASGI: translates ASGI scopes/events and returns ASGI responses;
- CLI: translates command line arguments into command/group execution.

This lets the framework reuse schemas, route registration, rules and lifecycle
hooks while changing only the transport.

## Routing Tree

`Itinerary` is the core route structure. It stores `Node` objects and exposes:

- `add_rule()` to register routes;
- `match()` / `get_current_route()` to resolve input;
- `to_url()` to build a path by route name.

Performance-sensitive details:

- routes are indexed by `(key, method)`;
- error handlers are indexed by status code;
- matching results are cached by route key, method and args;
- static children are ordered before dynamic children;
- adding the same named route twice updates the route instead of creating
  duplicates.

The same idea can power HTTP paths, REST controllers and CLI groups. A command
tree like `bookings remove 1` is conceptually the same as `/bookings/{id}`:
both are nested route segments with a terminal handler.

## OpenAPI From Schemas

API runtimes should not hand-write OpenAPI. Controllers, actions, request bodies,
parameters and response bodies already contain enough metadata. WSGI and ASGI
Swagger builders should therefore project the same route tree into OpenAPI paths
and components.

When an API is mounted under a prefix, generated paths must include the external
prefix. For example, an internal action `/bookings` mounted at `/api/v1` should
appear as `/api/v1/bookings` in OpenAPI.

## Rules And Properties

Rules should be attached to the same schema/route objects as the handler. That
makes permissions reusable across strategies:

- a page can hide or reject access;
- an API action can expose security requirements in OpenAPI;
- a CLI command can block execution before calling the handler.

The framework should keep this metadata declarative and close to the endpoint.
