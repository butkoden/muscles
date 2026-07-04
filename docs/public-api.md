# Muscles Public API Reference

Language: English  
Russian version: [public-api.ru.md](public-api.ru.md)

This document lists the public symbols exported by `muscles` / `muscles.core`
and documents helpers that are easy to miss when reading only feature guides.

Use this page as an API map. Topic guides such as `action-contract.en.md`,
`backend-framework.md`, `schema.md`, `dependency.md` and `configure.md` still
contain deeper examples.

## Runtime Mode Helpers

Runtime mode helpers normalize the environment used by framework packages and
generated applications.

```python
from muscles import RuntimeMode, app_runtime_mode, is_development, is_production, is_test, resolve_runtime_mode

mode = resolve_runtime_mode(config={"main": {"ENV": "test"}})
assert mode == RuntimeMode.TEST

assert app_runtime_mode(app, override="development") == RuntimeMode.DEVELOPMENT
assert is_development(app, override="dev") is True
assert is_test(app, override="test") is True
assert is_production(app, override="prod") is True
```

Resolution order:

1. Explicit `override`.
2. Environment variable `MUSCLES_ENV` by default.
3. `main.ENV` from a dict-like config or object with `get("main.ENV")`.
4. `RuntimeMode.PRODUCTION` fallback.

Accepted values are `dev`/`development`, `test`/`testing` and
`prod`/`production`.

## Application Registry Helpers

`ApplicationRegistry` is the app-scoped collection used by inspection,
protocol projections and extensions. It stores routes, schemas, rules, CLI
commands, actions, SQL metadata and emitted events.

```python
from muscles import ApplicationRegistry, get_application_registry

registry = get_application_registry(app)
registry.add_schema(BookingCreate)
registry.add_rule("bookings.public_create")
registry.emit_event("bookings.created", {"id": 1})

assert registry.get_events("bookings.created") == [{"id": 1}]
```

`get_application_registry(app)` creates `app.__muscles_registry__` on demand.
Passing `app=None` uses the process-level fallback registry for legacy code,
but framework integrations should prefer a real application instance to avoid
state leaks between apps and tests.

## Action Helpers

Actions are the protocol-neutral execution contract for HTTP, CLI, MCP,
JSON-RPC, SSE and extension packages.

```python
from muscles import ActionDispatcher, action, dispatch_action, register_action


def create_booking(payload, context):
    return {"title": payload["title"], "transport": context.transport}


register_action(
    app,
    name="bookings.create",
    input_schema={
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
    },
    transports=["http", "cli", "mcp"],
    handler=create_booking,
)

result = ActionDispatcher(app).execute(
    "bookings.create",
    {"title": "Discovery call"},
    transport="mcp",
)

same_result = dispatch_action(
    app,
    "bookings.create",
    {"title": "Discovery call"},
    transport="mcp",
)
```

`action(app, **options)` is the decorator form used internally by
`ApplicationMeta` so applications can use `@app.action(...)`.

Core action objects:

- `ActionContract` - public action metadata and handler reference.
- `ActionContext` - app, registry, selected action, transport and call metadata passed to handlers/rules.
- `ActionResult` - normalized result wrapper from `ActionDispatcher.execute(...)`.
- `ApplicationContract` - machine-readable inspection payload shape.

Core action errors:

- `ActionError` - base action error with `status`, `reason`, `data` and `error_type`.
- `ActionNotFound` - action name is not registered.
- `ActionValidationError` - JSON Schema validation failed.
- `ActionPermissionDenied` - transport/rule/security denied execution.
- `ActionExecutionError` - handler or rule raised an execution error.

## Stream Helpers

Streaming actions return `StreamResult` with `StreamEvent` items. The core event
types are `progress`, `log`, `result` and `error`.

```python
from muscles import StreamEvent, StreamResult, coerce_stream_event, stream_events


def source():
    yield {"type": "progress", "data": {"step": 1}}
    yield StreamEvent(type="result", data={"ok": True}, event_id="done")


result = StreamResult(source=source(), metadata={"backpressure": "bounded"})
events = list(stream_events(result))

assert events[0] == StreamEvent(type="progress", data={"step": 1})
assert coerce_stream_event({"event": "log", "message": "legacy"}).type == "log"
```

`stream_events(...)` accepts either a `StreamResult` or an iterable of
`StreamEvent` / mapping items. It normalizes legacy mappings, turns source
errors into `StreamEvent(type="error", data={...})` and calls `close()` /
`close_source()` when available.

## Dependency APIs

For new framework integrations, prefer `DependencyContainer`. It supports app,
request and transient scopes without relying on global mutable dependency state.

```python
from muscles import DependencyContainer


class StoreInterface:
    pass


class Store(StoreInterface):
    pass


container = DependencyContainer()
container.register(StoreInterface, Store, scope=DependencyContainer.REQUEST)

request_scope = container.create_scope()
store = request_scope.resolve(StoreInterface)
```

Scopes:

- `DependencyContainer.APP` / `"app"` - one instance per container.
- `DependencyContainer.REQUEST` / `"request"` - one instance per created scope.
- `DependencyContainer.TRANSIENT` / `"transient"` - new instance on every resolve.

Legacy dependency APIs remain public for compatibility:

- `DependencyStorage` - global dependency storage.
- `Dependency` - descriptor/context helper and `Dependency.resolve(...)`.
- `inject` - decorator that injects dependencies by annotation or default value.
- `DependencyScope` - request scope object created by `DependencyContainer.create_scope()`.

## Backend Pipeline

`BackendPipeline` is the transport-neutral execution helper used by ASGI/WSGI
adapters. It owns framework-level handler binding while transports keep protocol
parsing and serialization.

```python
from muscles import BackendPipeline

pipeline = BackendPipeline(container=container)
kwargs = pipeline.build_handler_kwargs(handler, request, route_params={"booking_id": "1"})
```

Important methods:

- `header_lookup(headers, name)` - case/underscore-insensitive header lookup.
- `coerce_value(annotation, value)` - primitive path/query/header coercion.
- `coerce_body(annotation, payload)` - dict payload to Pydantic/dataclass/class object.
- `resolve_dependency(annotation, request=None)` - request container, app container, legacy DI fallback.
- `build_handler_kwargs(handler, request, route_params)` - binds request, route params, body, query, headers, cookies and dependencies.
- `run_guards(...)` / `run_guards_async(...)` - route guard execution.
- `run_security(...)` / `run_security_async(...)` - route security execution.
- `call_route_handler(...)` / `call_route_handler_async(...)` - middleware chain and handler call.

## Response Helpers

Core response helpers let runtime adapters normalize handler return values
without duplicating behavior.

```python
from muscles import BaseResponse, BytesResponse, FileResponse, HtmlResponse, JsonResponse, NoContentResponse, normalize_response

assert isinstance(normalize_response({"ok": True}), JsonResponse)
assert isinstance(normalize_response("<h1>Hello</h1>"), HtmlResponse)
assert isinstance(normalize_response(b"raw"), BytesResponse)
assert isinstance(normalize_response(None), NoContentResponse)

response = normalize_response(({"created": True}, 201, {"X-Request-Id": "abc"}))
assert response.status == 201
```

`normalize_response(...)` accepts:

- `BaseResponse` instances;
- `(body, status)` and `(body, status, headers)` tuples;
- `bytes`, `str`, mappings and `None`;
- any other object as `text/plain`.

`FileResponse` reads a file path, guesses MIME type and sets
`Content-Disposition`; `BaseResponse.with_content_length()` ensures
`Content-Length`.

## Problem Details And Exceptions

`normalize_problem_payload(...)` creates RFC 7807-style problem payloads from
core/domain exceptions.

```python
from muscles import RequestErrorException, normalize_problem_payload

payload = normalize_problem_payload(
    RequestErrorException(status=422, reason="Invalid body"),
    request=type("Request", (), {"path": "/api/bookings"})(),
)

assert payload["status"] == 422
assert payload["instance"] == "/api/bookings"
```

Public exception classes:

- `ErrorException` - base domain/framework exception with `status`, `reason`, `body`, `traceback`.
- `ApplicationException` - generic application/runtime failure, default status `500`.
- `AccessDeniedException` - access denied, default status `403`.
- `RequestErrorException` - request-level error.
- `NotFoundException`, `IsExistsException`, `UpdateErrorException`, `InsertErrorException`, `NotAuthenticationException`, `AttributeErrorException`, `ModelException` - compatibility/domain error types.

## CORS Helpers

`CorsMiddleware` and `cors(...)` provide a small transport-neutral CORS helper.
ASGI/WSGI adapters can call it as middleware or use `preflight_response(...)`.

```python
from muscles import cors

middleware = cors(
    allow_origins=["https://app.example"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=600,
)

response = middleware(request, call_next)
preflight = middleware.preflight_response(request)
```

`CorsMiddleware.apply(response, request)` normalizes the response and adds
`Access-Control-Allow-*` headers.

## Canonical Route Helpers

Canonical route helpers keep docs/schema/health URLs consistent across
runtimes and generated projects.

```python
from muscles import CANONICAL_ALIASES, CANONICAL_ROUTES, build_route_aliases, canonical_alias_pairs, normalize_path

assert normalize_path("/api/", "/v1", "docs") == "/api/v1/docs"

mapping = build_route_aliases(prefix="/api")
assert mapping["canonical"]["openapi"] == "/api/openapi.json"
assert mapping["aliases"]["/api/swagger"] == "/api/docs"

pairs = canonical_alias_pairs(prefix="/api")
assert pairs["/api/docs"] == ["/api/swagger"]
```

Canonical routes:

- `CANONICAL_ROUTES["openapi"] == "/openapi.json"`
- `CANONICAL_ROUTES["docs"] == "/docs"`
- `CANONICAL_ROUTES["redoc"] == "/redoc"`
- `CANONICAL_ROUTES["healthz"] == "/healthz"`
- `CANONICAL_ROUTES["ready"] == "/ready"`
- `CANONICAL_ROUTES["live"] == "/live"`

Compatibility aliases:

- `CANONICAL_ALIASES["schema"] -> "/openapi.json"`
- `CANONICAL_ALIASES["swagger"] -> "/docs"`
- `CANONICAL_ALIASES["health"] -> "/healthz"`

## Generator Provider Contract

`GeneratorRegistry` is the core registry for generator providers used by CLI
and project scaffolding packages.

```python
from pathlib import Path
from muscles import GenerationRequest, GeneratorProvider, GeneratorRegistry


class PageGenerator:
    name = "page"

    def supports(self, generator_type: str) -> bool:
        return generator_type == "page"

    def generate(self, project_root: Path, request: GenerationRequest) -> list[str]:
        return [str(project_root / "app" / "web" / f"{request.name}.py")]


registry = GeneratorRegistry()
registry.register(PageGenerator())
provider = registry.resolve("page")
created_files = provider.generate(Path("."), GenerationRequest("page", "Home", with_tests=True))
```

`GeneratorRegistry.register(...)` ignores duplicate provider names. `resolve(...)`
raises `ValueError` when no provider supports the requested generator type.

## Storage Compatibility APIs

The storage mapper APIs are public compatibility helpers. New integrations
should usually prefer explicit application registries or dependency containers.

```python
from muscles import Storage, StorageMapper, StorageStrategy, storageMapper


class Service:
    pass


storageMapper.add("service", Service, ignore_if_exists=True)
service = storageMapper.get("service")
```

Public storage symbols:

- `Storage` - singleton-like key/value class storage.
- `StorageStrategy` - object construction strategy for classes in storage.
- `StorageMapper` - helper that stores classes and constructs instances.
- `storageMapper` - module-level compatibility mapper instance.
- `StorageInterface`, `EventsStorageInterface`, `EventsStorage` - legacy storage interfaces/classes.

## Schema And Field Exports

Core schema exports are documented in `schema.md` and related guides. The
public export list includes:

- Schema base and OpenAPI bodies: `Schema`, `RequestBody`, `JsonRequestBody`, `XmlRequestBody`, `FormRequestBody`, `FileRequestBody`, `MultipartRequestBody`, `TextRequestBody`, `PayloadRequestBody`, `ResponseBody`, `JsonResponseBody`, `XmlResponseBody`, `HtmlResponseBody`, `TextResponseBody`.
- Parameters: `BaseParameter`, `PathParameter`, `FormParameter`, `QueryParameter`, `CookieParameter`, `HeaderParameter`.
- Security: `BaseSecurity`, `BasicAuthSecurity`, `BearerAuthSecurity`, `BearerJwtAuth`, `ApiKeyAuthSecurity`.
- Routing/model containers: `Itinerary`, `Swagger`, `BaseModel`, `Model`, `ModelStorage`, `BaseGroup`, `BaseCollection`, `Collection`, `BaseColumn`, `Column`.
- Fields: `Boolean`, `List`, `Email`, `Phone`, `Time`, `Enum`, `Float`, `Double`, `Binary`, `Json`, `String`, `Numeric`, `SmallInteger`, `Integer`, `Date`, `File`, `Text`, `DateTime`, `Timestamp`, `BigInteger`, `UUID4`, `Key`.
- Users: `BaseUser`, `RobotUser`, `SystemUser`, `GuestUser`, `User`.

## Pydantic Bridge Helpers

The Pydantic bridge is optional. It lets integration packages convert Muscles
models to JSON Schema / Pydantic models without making Pydantic a hard runtime
dependency for the core package.

```python
from muscles.core.schema import from_pydantic_instance, pydantic_available, to_json_schema, to_pydantic_model

schema = to_json_schema(BookingCreate)

if pydantic_available():
    PydanticBookingCreate = to_pydantic_model(BookingCreate)
    instance = PydanticBookingCreate(title="Call")
    muscles_model = from_pydantic_instance(BookingCreate, instance)
```

Helpers:

- `pydantic_available()` - returns `True` when Pydantic can be imported.
- `to_json_schema(model_cls_or_instance)` - returns Muscles model column metadata as JSON Schema.
- `to_pydantic_model(model_cls)` - builds a Pydantic model class from Muscles columns.
- `from_pydantic_instance(model_cls, pydantic_instance)` - creates a Muscles model instance from a Pydantic v2 instance.

## Value Objects

Value objects normalize and validate domain values before they enter handlers,
schemas or persistence layers.

```python
from muscles import EmailValue, MoneyValue, PercentageValue, SlugValue, UtcDateTimeValue

assert EmailValue.parse("USER@Example.COM").to_primitive() == "user@example.com"
assert SlugValue("hello-world").value == "hello-world"
assert PercentageValue("12.5").to_primitive() == 12.5
assert MoneyValue({"amount": "10.00", "currency": "usd"}).to_primitive() == {"amount": "10.00", "currency": "USD"}
assert UtcDateTimeValue("2026-01-01T10:00:00+03:00").to_primitive().endswith("Z")
```

Public value object exports:

- `ValueObject` - immutable base with `parse(...)`, `normalize(...)`, `validate(...)`, `value` and `to_primitive()`.
- `EmailValue`, `PhoneValue`, `DateRangeValue`, `NonEmptyStringValue`, `SlugValue`, `UrlValue`, `CountryCodeValue`, `PercentageValue`, `MoneyValue`, `UtcDateTimeValue`, `DateTimeRangeValue`.
- `ValueObjectField` - schema field for value object-backed values.

## Application And Context Exports

Application/context symbols are documented in `architecture.md`, `context.md`
and `instance.md`:

- `Application`, `ApplicationMeta`, `PackageMeta`;
- `BaseStrategy`, `Context`;
- `Configurator`;
- `Self`;
- `inspect_application`.

## Support Exports

Additional support exports:

- `Watchdog`, `WatchdogHandlerInterface` - filesystem/runtime watchdog helpers.
- `BaseResponseHandler`, `ResponseHandler` - response handler compatibility classes.
