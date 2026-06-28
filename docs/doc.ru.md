# Документация Muscles Core

Язык: русский  
English version: [doc.md](doc.md)

Это каноническая точка входа в документацию ядра Muscles. Тематические файлы
остаются глубокими справочниками, но новое поведение core должно отражаться
здесь и в английской версии.

## Что Даёт Muscles Core

`muscles` - общий core-пакет экосистемы Muscles. В нём находятся:

- жизненный цикл приложения;
- конфигурация и helpers runtime mode;
- dependency injection;
- контракты context и strategy;
- schemas, fields, value objects и OpenAPI metadata;
- общее дерево маршрутов (`Itinerary`);
- helpers нормализации response;
- backend framework primitives для ASGI и WSGI runtimes.

Пакеты `muscles-asgi`, `muscles-wsgi` и `muscles-cli` проецируют эти core-
контракты в конкретные протоколы.

## Расширения Экосистемы

Core намеренно хранит protocol-neutral contracts. Runtime и integration
repositories расширяют эти контракты:

- [`muscles-asgi`](https://github.com/butkoden/muscles-asgi) - ASGI runtime,
  async request/response handling, REST API projection, OpenAPI/Swagger UI,
  ASGI `TestClient`, file uploads и CORS preflight поверх core routing.
- [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) - WSGI runtime,
  request/response handling, page/template support, static files, REST API
  projection, OpenAPI/Swagger UI, uploads и CORS preflight поверх core routing.
- [`muscles-cli`](https://github.com/butkoden/muscles-cli) - CLI projection той
  же application model, command/group routing и project scaffolding.
- [`muscles-sql`](https://github.com/butkoden/muscles-sql) - SQL-oriented
  persistence extension для приложений с database integration.
- [`muscles-jsonrpc`](https://github.com/butkoden/muscles-jsonrpc) - JSON-RPC
  protocol projection для core actions и application contracts.
- [`muscles-sse`](https://github.com/butkoden/muscles-sse) - Server-Sent Events
  projection для streaming action results.
- [`muscles-otel`](https://github.com/butkoden/muscles-otel) - observability
  extension для OpenTelemetry-style instrumentation.
- [`muscles-mcp`](https://github.com/butkoden/muscles-mcp) - MCP projection,
  который exposes core application actions as tools.
- [`muscular-example`](https://github.com/butkoden/muscular-example) - example
  application, где видно, как ecosystem packages работают вместе.

Когда добавляется core feature, здесь нужно описывать protocol-neutral contract,
а runtime-specific examples добавлять в репозиторий расширения, который этот
контракт исполняет.

## Установка

Текущий канонический способ установки - GitHub source install:

```bash
pip install git+https://github.com/butkoden/muscles.git
```

Для web/API runtime используйте отдельные runtime-пакеты:

```bash
pip install git+https://github.com/butkoden/muscles-asgi.git
pip install git+https://github.com/butkoden/muscles-wsgi.git
```

Подробнее: [installation.md](installation.md).

## Форма Приложения

Обычно Muscles-приложение - это класс с `ApplicationMeta`, `Configurator` и
`Context`:

```python
from muscles import ApplicationMeta, Configurator, Context


class App(metaclass=ApplicationMeta):
    config = Configurator(obj={"main": {"DEBUG": True}})
    context = Context(MyStrategy, params={})

    def run(self, *args):
        return self.context.execute(*args, shutup=True)
```

`Context` отвечает за выполнение runtime и lifecycle hooks. Strategy-пакеты
решают, как перевести внешний input в этот общий application contract.

Подробнее: [architecture.md](architecture.md), [context.md](context.md),
[instance.md](instance.md).

## Golden Path Структура Проекта

Рекомендуемая структура приложения:

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

HTTP, CLI и другие entry handlers должны оставаться тонкими. Общую бизнес-
логику держите в domain services и value objects.

Подробнее: [golden-path.md](golden-path.md),
[golden-tutorial.md](golden-tutorial.md).

## Routing И API Modules

`Itinerary` - core route tree. Он регистрирует маршруты, матчинг путей, сборку
URL и хранение route metadata. Runtime-пакеты используют эту структуру для HTTP
routes, REST controllers, static routes и CLI command trees.

Route groups добавляют общий prefix и metadata:

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

ASGI и WSGI OpenAPI builders используют metadata группы для tags, security и
common responses.

Подробнее: [backend-framework.md](backend-framework.md).

## Middleware, Guards И CORS

`use()` регистрирует middleware. Middleware получает `(request, call_next)` и
возвращает response:

```python
def audit_middleware(request, call_next):
    response = call_next(request)
    return response


api.use(audit_middleware)
```

`guard()` регистрирует route guard по path pattern:

```python
def require_auth(request):
    if request.user.is_guest():
        return {"error": "unauthorized"}, 401


api.guard("/api/**", require_auth, except_=["/api/public/**"])
```

CORS доступен как общий middleware:

```python
from muscles import cors

api.use(cors(
    allow_origins=["https://app.example"],
    allow_credentials=True,
))
```

ASGI и WSGI runtimes используют один и тот же CORS middleware для обычных
ответов и `OPTIONS` preflight responses.

## Auth И Error Mapping

`BearerAuthSecurity` описывает HTTP bearer auth для OpenAPI. `BearerJwtAuth`
добавляет небольшой HS256 JWT provider:

```python
from muscles import BearerJwtAuth

jwt_auth = BearerJwtAuth(secret=settings.jwt_secret, subject="sub")
token = jwt_auth.issue({"sub": "user-1"})
auth_result = jwt_auth.authenticate_header(f"Bearer Bearer {token}")
```

`authenticate_header()` принимает дублирующийся bearer prefix для совместимости
с legacy clients и возвращает `payload`, `token` и `user`. У возвращаемого user
есть `uid`, взятый из настроенного subject claim.

Domain exceptions можно привязать к HTTP statuses:

```python
api.map_error(PermissionError, status=403)
api.map_error(ValueError, status=422)
```

ASGI и WSGI сохраняют mapped statuses, когда handler выбрасывает mapped
exception.

## Responses

Core response helpers нормализуются runtime-пакетами:

```python
from muscles import BytesResponse, FileResponse, JsonResponse, NoContentResponse

return JsonResponse({"ok": True})
return NoContentResponse()
return BytesResponse(b"PNG", content_type="image/png")
return FileResponse("/tmp/report.pdf", as_attachment=True)
```

`None` превращается в `204 No Content`, mappings - в JSON, strings - в HTML,
bytes - в `application/octet-stream`.

## Schemas, Models И OpenAPI

Schema classes описывают данные один раз и переиспользуются runtime-
проекциями:

```python
from muscles import Column, Key, Model, String


class Document(Model):
    id = Column(Key)
    title = Column(String, required=True)
```

Request bodies, response bodies и parameters используются ASGI и WSGI OpenAPI
builders.

Подробнее: [schema.md](schema.md).

## Dependency Injection

Core DI строится на `Dependency`, `DependencyStorage` и `inject()`:

```python
from muscles import Dependency


class StoreInterface:
    pass


@Dependency.init(StoreInterface)
class Store(StoreInterface):
    pass
```

Runtime handler pipelines могут резолвить аннотированные зависимости из этого
core-контейнера.

Подробнее: [dependency.md](dependency.md).

## Конфигурация И Runtime Mode

`Configurator` читает конфигурацию проекта. Runtime mode helpers задают
поведение для development, test и production.

Подробнее: [configure.md](configure.md).

## Actions

Core actions - protocol-neutral contracts. Их можно проецировать в HTTP, CLI,
MCP, JSON-RPC, SSE и другие runtime layers через `ActionDispatcher`.

Подробнее:

- [action-contract.en.md](action-contract.en.md)
- [action-contract.ru.md](action-contract.ru.md)

## Тестирование Core Из Исходников

Из core-репозитория:

```bash
PYTHONPATH=src python3 -m pytest
```

Для ecosystem packages из соседних checkout:

```bash
PYTHONPATH=../muscles/src:src python3 -m pytest
```

## Глубокие Справочники

- Документация runtime-репозиториев:
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
