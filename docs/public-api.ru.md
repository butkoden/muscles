# Справочник публичного API Muscles

Язык: русский  
English version: [public-api.md](public-api.md)

Этот документ закрывает публичные символы, которые экспортируются из
`muscles` / `muscles.core`, но не всегда видны из тематических гайдов.

## Runtime Mode

Функции режима выполнения помогают одинаково определять окружение в core,
runtime-пакетах и generated-приложениях.

```python
from muscles import RuntimeMode, app_runtime_mode, is_development, is_production, is_test, resolve_runtime_mode

mode = resolve_runtime_mode(config={"main": {"ENV": "test"}})
assert mode == RuntimeMode.TEST

assert app_runtime_mode(app, override="development") == RuntimeMode.DEVELOPMENT
assert is_development(app, override="dev") is True
assert is_test(app, override="test") is True
assert is_production(app, override="prod") is True
```

Порядок выбора режима:

1. `override`.
2. Переменная окружения `MUSCLES_ENV`.
3. `main.ENV` из config.
4. `RuntimeMode.PRODUCTION` по умолчанию.

## Application Registry

`ApplicationRegistry` хранит app-scoped metadata: routes, schemas, rules, CLI,
actions, SQL metadata и события. Протоколы и extension-пакеты читают эти данные
через `inspect_application(app)` и `get_application_registry(app)`.

```python
from muscles import ApplicationRegistry, get_application_registry

registry = get_application_registry(app)
registry.add_schema(BookingCreate)
registry.add_rule("bookings.public_create")
registry.emit_event("bookings.created", {"id": 1})
```

`get_application_registry(app)` создаёт `app.__muscles_registry__` при первом
обращении. `app=None` использует fallback registry и нужен только для legacy
сценариев.

## Actions

Actions - протокольно-независимые контракты приложения. HTTP, CLI, MCP,
JSON-RPC, SSE и extensions должны исполнять их через `ActionDispatcher`.

```python
from muscles import ActionDispatcher, dispatch_action, register_action


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

result = ActionDispatcher(app).execute("bookings.create", {"title": "Call"}, transport="mcp")
same_result = dispatch_action(app, "bookings.create", {"title": "Call"}, transport="mcp")
```

Публичные action-типы:

- `ActionContract` - metadata действия.
- `ActionContext` - application, registry, action, transport и metadata вызова.
- `ActionResult` - нормализованный результат `ActionDispatcher.execute(...)`.
- `ApplicationContract` - shape machine-readable inspection payload.
- `action(app, **options)` - decorator form, используемый `@app.action(...)`.

Ошибки actions: `ActionError`, `ActionNotFound`, `ActionValidationError`,
`ActionPermissionDenied`, `ActionExecutionError`.

## Streams

Streaming actions возвращают `StreamResult` с событиями `StreamEvent`.
Допустимые типы событий: `progress`, `log`, `result`, `error`.

```python
from muscles import StreamEvent, StreamResult, coerce_stream_event, stream_events

result = StreamResult(
    source=[
        {"type": "progress", "data": {"step": 1}},
        StreamEvent(type="result", data={"ok": True}),
    ],
)

events = list(stream_events(result))
```

`coerce_stream_event(...)` преобразует mapping в `StreamEvent`.
`stream_events(...)` нормализует поток, превращает ошибки источника в
`StreamEvent(type="error", ...)` и закрывает source через `close()` /
`close_source()`.

## Dependency APIs

Для новых интеграций используйте `DependencyContainer`: он поддерживает scopes
без глобального mutable-state.

```python
from muscles import DependencyContainer

container = DependencyContainer()
container.register(StoreInterface, Store, scope=DependencyContainer.REQUEST)

scope = container.create_scope()
store = scope.resolve(StoreInterface)
```

Scopes:

- `DependencyContainer.APP` / `"app"` - один instance на container.
- `DependencyContainer.REQUEST` / `"request"` - один instance на request scope.
- `DependencyContainer.TRANSIENT` / `"transient"` - новый instance на каждый `resolve`.

Legacy API остаётся публичным для совместимости: `DependencyStorage`,
`Dependency`, `inject`, `DependencyScope`.

## Backend Pipeline

`BackendPipeline` - общий backend execution helper для ASGI/WSGI. Он связывает
handler arguments, dependencies, guards, security и middleware; протоколы
остаются ответственными за parsing request и serialization response.

Ключевые методы:

- `header_lookup(headers, name)`.
- `coerce_value(annotation, value)`.
- `coerce_body(annotation, payload)`.
- `resolve_dependency(annotation, request=None)`.
- `build_handler_kwargs(handler, request, route_params)`.
- `run_guards(...)` / `run_guards_async(...)`.
- `run_security(...)` / `run_security_async(...)`.
- `call_route_handler(...)` / `call_route_handler_async(...)`.

## Responses

Response helpers нормализуют значения handlers в response objects.

```python
from muscles import BytesResponse, HtmlResponse, JsonResponse, NoContentResponse, normalize_response

assert isinstance(normalize_response({"ok": True}), JsonResponse)
assert isinstance(normalize_response("<h1>Hello</h1>"), HtmlResponse)
assert isinstance(normalize_response(b"raw"), BytesResponse)
assert isinstance(normalize_response(None), NoContentResponse)
```

`normalize_response(...)` принимает `BaseResponse`, tuple-формы
`(body, status)` / `(body, status, headers)`, `bytes`, `str`, mappings, `None`
и fallback-объекты. Также публичны `BaseResponse`, `FileResponse`.

## Problem Details And Exceptions

`normalize_problem_payload(...)` собирает RFC 7807-style payload из exceptions.

```python
from muscles import RequestErrorException, normalize_problem_payload

payload = normalize_problem_payload(RequestErrorException(status=422, reason="Invalid body"))
```

Публичные exception-типы: `ErrorException`, `ApplicationException`,
`AccessDeniedException`, `RequestErrorException`, `NotFoundException`,
`IsExistsException`, `UpdateErrorException`, `InsertErrorException`,
`NotAuthenticationException`, `AttributeErrorException`, `ModelException`.

## CORS

`CorsMiddleware` и `cors(...)` дают небольшой transport-neutral CORS helper.

```python
from muscles import cors

middleware = cors(allow_origins=["https://app.example"], allow_credentials=True)
response = middleware(request, call_next)
preflight = middleware.preflight_response(request)
```

## Canonical Routes

Canonical route helpers синхронизируют URL документации, OpenAPI и health
checks между runtimes.

```python
from muscles import CANONICAL_ALIASES, CANONICAL_ROUTES, build_route_aliases, canonical_alias_pairs, normalize_path

assert normalize_path("/api/", "/v1", "docs") == "/api/v1/docs"
assert build_route_aliases(prefix="/api")["aliases"]["/api/swagger"] == "/api/docs"
```

Публичные helpers: `CANONICAL_ROUTES`, `CANONICAL_ALIASES`, `normalize_path`,
`build_route_aliases`, `canonical_alias_pairs`.

## Generator Provider Contract

`GeneratorRegistry` хранит providers для генераторов CLI/scaffolding.

```python
from muscles import GenerationRequest, GeneratorRegistry

registry = GeneratorRegistry()
registry.register(PageGenerator())
provider = registry.resolve("page")
files = provider.generate(project_root, GenerationRequest("page", "Home", with_tests=True))
```

Публичные типы: `GenerationRequest`, `GeneratorProvider`, `GeneratorRegistry`.

## Storage Compatibility

Storage API оставлен публичным для совместимости. Для новых интеграций чаще
лучше использовать `ApplicationRegistry` или `DependencyContainer`.

Публичные symbols: `Storage`, `StorageStrategy`, `StorageMapper`,
`storageMapper`, `StorageInterface`, `EventsStorageInterface`, `EventsStorage`.

## Schema, Fields And Users

Schema API подробно описан в [schema.md](schema.md). Экспортируются:

- Bodies: `Schema`, `RequestBody`, `JsonRequestBody`, `XmlRequestBody`,
  `FormRequestBody`, `FileRequestBody`, `MultipartRequestBody`,
  `TextRequestBody`, `PayloadRequestBody`, `ResponseBody`,
  `JsonResponseBody`, `XmlResponseBody`, `HtmlResponseBody`, `TextResponseBody`.
- Parameters: `BaseParameter`, `PathParameter`, `FormParameter`,
  `QueryParameter`, `CookieParameter`, `HeaderParameter`.
- Security: `BaseSecurity`, `BasicAuthSecurity`, `BearerAuthSecurity`,
  `BearerJwtAuth`, `ApiKeyAuthSecurity`.
- Containers: `Itinerary`, `Swagger`, `BaseModel`, `Model`, `ModelStorage`,
  `BaseGroup`, `BaseCollection`, `Collection`, `BaseColumn`, `Column`.
- Fields: `Boolean`, `List`, `Email`, `Phone`, `Time`, `Enum`, `Float`,
  `Double`, `Binary`, `Json`, `String`, `Numeric`, `SmallInteger`, `Integer`,
  `Date`, `File`, `Text`, `DateTime`, `Timestamp`, `BigInteger`, `UUID4`,
  `Key`.
- Users: `BaseUser`, `RobotUser`, `SystemUser`, `GuestUser`, `User`.

## Pydantic Bridge

Pydantic bridge helpers не делают Pydantic обязательной зависимостью core.

```python
from muscles.core.schema import from_pydantic_instance, pydantic_available, to_json_schema, to_pydantic_model

schema = to_json_schema(BookingCreate)
if pydantic_available():
    PydanticBookingCreate = to_pydantic_model(BookingCreate)
```

Публичные helpers: `pydantic_available`, `to_json_schema`,
`to_pydantic_model`, `from_pydantic_instance`.

## Value Objects

Value objects нормализуют и валидируют доменные значения.

Публичные symbols: `ValueObject`, `EmailValue`, `PhoneValue`, `DateRangeValue`,
`NonEmptyStringValue`, `SlugValue`, `UrlValue`, `CountryCodeValue`,
`PercentageValue`, `MoneyValue`, `UtcDateTimeValue`, `DateTimeRangeValue`,
`ValueObjectField`.

## Application And Support

Application/context API: `Application`, `ApplicationMeta`, `PackageMeta`,
`BaseStrategy`, `Context`, `Configurator`, `Self`, `inspect_application`.

Support API: `Watchdog`, `WatchdogHandlerInterface`, `BaseResponseHandler`,
`ResponseHandler`.
