# Документация ядра Muscles

Язык: русский  
Английская версия: [doc.md](doc.md)

Это каноническая точка входа в документацию ядра Muscles. Тематические файлы
остаются глубокими справочниками, но новое поведение ядра должно отражаться
здесь и в английской версии.

## Что дает ядро Muscles

`muscles` - общий пакет ядра экосистемы Muscles. В нём находятся:

- жизненный цикл приложения;
- конфигурация и помощники режима выполнения;
- внедрение зависимостей;
- контракты контекста и стратегий;
- схемы, поля, value objects и метаданные OpenAPI;
- общее дерево маршрутов (`Itinerary`);
- помощники нормализации ответов;
- backend-примитивы для ASGI и WSGI.

Пакеты `muscles-asgi`, `muscles-wsgi` и `muscles-cli` проецируют эти контракты
ядра в конкретные протоколы.
Пакеты `muscles-ai`, `muscles-documents`, `muscles-sql` и `muscles-otel`
добавляют переиспользуемые возможности фреймворка, не меняя общую модель
приложения.

## Справочник по репозиториям экосистемы

Ядро намеренно хранит контракты, не завязанные на конкретный протокол.
Репозитории рантаймов, протоколов и интеграций расширяют эти контракты.
Используйте таблицы ниже как быстрый справочник, когда нужно понять, где должно
жить поведение.

### Рантаймы и протокольные расширения

[`muscles-asgi`](https://github.com/butkoden/muscles-asgi) - ASGI-рантайм
поверх маршрутизации и схем ядра. Используйте его для асинхронных
HTTP-приложений, REST API, OpenAPI/Swagger UI, типизированного вызова
обработчиков, загрузки файлов, CORS preflight и ASGI `TestClient`.

[`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) - WSGI-рантайм
поверх маршрутизации и схем ядра. Используйте его для классических
WSGI-приложений, страниц и шаблонов, статических файлов, REST API,
OpenAPI/Swagger UI, загрузки файлов и CORS preflight.

[`muscles-cli`](https://github.com/butkoden/muscles-cli) проецирует ту же
модель приложения в CLI-команды. Используйте его для маршрутизации команд и
групп, локальных инструментов разработчика и генерации структуры проекта по
golden path.

[`muscles-jsonrpc`](https://github.com/butkoden/muscles-jsonrpc) публикует
действия ядра и контракты приложения как JSON-RPC-методы.

[`muscles-sse`](https://github.com/butkoden/muscles-sse) доставляет потоковые
результаты действий через Server-Sent Events.

[`muscles-mcp`](https://github.com/butkoden/muscles-mcp) публикует действия
приложения как MCP-инструменты.

### Данные, наблюдаемость и интеграции

[`muscles-sql`](https://github.com/butkoden/muscles-sql) - SQL-расширение для
хранения данных. Используйте его для интеграции с базами данных и паттернов
хранения, которые не должны жить внутри протокольных рантаймов.

[`muscles-otel`](https://github.com/butkoden/muscles-otel) - расширение для
наблюдаемости. Используйте его для OpenTelemetry-инструментации, трассировок и
метрик вокруг ядра и рантаймов.

[`muscles-documents`](https://github.com/butkoden/muscles-documents) -
расширение для документов. Используйте его для загрузки локальных,
markdown/text-документов, парсинга, чанкинга и планирования синхронизации через
Muscles actions.

[`muscles-ai`](https://github.com/butkoden/muscles-ai) - AI/RAG-расширение.
Используйте его для read-only ответов на вопросы, retrieval и AI-диагностики
через ту же модель actions/dispatcher, что используют протокольные проекции.

### Примеры, совместимость и поддерживающие репозитории

[`muscular-example`](https://github.com/butkoden/muscular-example) - пример
приложения, в котором видно, как ядро, рантаймы и расширения собираются вместе.

[`muscles-benchmarks`](https://github.com/butkoden/muscles-benchmarks) -
рабочая область для бенчмарков маршрутизации, DI и изменений в рантаймах.

[`muscles-landing`](https://github.com/butkoden/muscles-landing) содержит
публичный сайт продукта и документации.

[`muscular-asgi`](https://github.com/butkoden/muscular-asgi) - устаревший
ASGI-пакет для совместимости и исторических проверок, пока экосистема сходится
на `muscles-asgi`.

Когда добавляется новая функция ядра, здесь нужно описывать независимый от
протокола контракт, а примеры для конкретного рантайма добавлять в репозиторий
расширения, который этот контракт исполняет.
Подробная карта ответственности: [repositories.md](repositories.md).

## Установка

Текущий канонический способ установки - установка из GitHub-репозитория:

```bash
pip install git+https://github.com/butkoden/muscles.git
```

Для web/API-приложений используйте отдельные рантайм-пакеты:

```bash
pip install git+https://github.com/butkoden/muscles-asgi.git
pip install git+https://github.com/butkoden/muscles-wsgi.git
```

Для переиспользуемых возможностей фреймворка подключайте extension-пакеты:

```bash
pip install git+https://github.com/butkoden/muscles-documents.git
pip install git+https://github.com/butkoden/muscles-ai.git
pip install git+https://github.com/butkoden/muscles-sql.git
pip install git+https://github.com/butkoden/muscles-otel.git
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

`Context` отвечает за выполнение рантайма и хуки жизненного цикла. Пакеты
стратегий решают, как перевести внешний ввод в общий контракт приложения.

Подробнее: [architecture.md](architecture.md), [context.md](context.md),
[instance.md](instance.md).

## Структура проекта Golden Path

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

HTTP, CLI и другие входные обработчики должны оставаться тонкими. Общую
бизнес-логику держите в доменных сервисах и объектах-значениях.

Подробнее: [golden-path.md](golden-path.md),
[golden-tutorial.md](golden-tutorial.md).

## Маршрутизация и API-модули

`Itinerary` - дерево маршрутов ядра. Он регистрирует маршруты, сопоставляет
пути, собирает URL и хранит метаданные маршрутов. Рантайм-пакеты используют
эту структуру для HTTP-маршрутов, REST-контроллеров, статических маршрутов и
деревьев CLI-команд.

Группы маршрутов добавляют общий префикс и метаданные:

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

Сборщики OpenAPI в ASGI и WSGI используют метаданные группы для `tags`,
`security` и общих `responses`.

Авторизацию endpoint можно переопределить поверх группы:

```python
@api.init("/api/login", method="post", auth=False)
def login(request):
    return {"token": "issued-token"}
```

Используйте `auth=False` для публичных endpoint внутри защищённых групп
маршрутов. Используйте `auth=[...]`, чтобы заменить унаследованную схему
безопасности для одного endpoint.

Подробнее: [backend-framework.md](backend-framework.md).

## Middleware, guards и CORS

`use()` регистрирует middleware. Middleware получает `(request, call_next)` и
возвращает ответ:

```python
def audit_middleware(request, call_next):
    response = call_next(request)
    return response


api.use(audit_middleware)
```

`guard()` регистрирует проверку маршрута по шаблону пути:

```python
def require_auth(request):
    if request.user.is_guest():
        return {"error": "unauthorized"}, 401


api.guard("/api/**", require_auth, except_=["/api/public/**"])
```

Когда отдельный endpoint вроде `/api/login` намеренно остаётся публичным,
лучше использовать `auth=False`, а не раздувать список `except_`.

CORS доступен как общий middleware:

```python
from muscles import cors

api.use(cors(
    allow_origins=["https://app.example"],
    allow_credentials=True,
))
```

ASGI и WSGI используют один и тот же CORS middleware для обычных ответов и
`OPTIONS` preflight-ответов.

## Аутентификация и сопоставление ошибок

`BearerAuthSecurity` описывает HTTP bearer-аутентификацию для OpenAPI.
`BearerJwtAuth` добавляет небольшой HS256 JWT-провайдер:

```python
from muscles import BearerJwtAuth

jwt_auth = BearerJwtAuth(secret=settings.jwt_secret, subject="sub")
token = jwt_auth.issue({"sub": "user-1"})
auth_result = jwt_auth.authenticate_header(f"Bearer Bearer {token}")
```

`authenticate_header()` принимает дублирующийся bearer-префикс для
совместимости с legacy-клиентами и возвращает `payload`, `token` и `user`.
У возвращаемого `user` есть `uid`, взятый из настроенного claim `subject`.

Доменные исключения можно привязать к HTTP-статусам:

```python
api.map_error(PermissionError, status=403)
api.map_error(ValueError, status=422)
```

ASGI и WSGI сохраняют назначенные статусы, когда handler выбрасывает
сопоставленное исключение.

## Ответы

Помощники ответов ядра нормализуются рантайм-пакетами:

```python
from muscles import BytesResponse, FileResponse, JsonResponse, NoContentResponse

return JsonResponse({"ok": True})
return NoContentResponse()
return BytesResponse(b"PNG", content_type="image/png")
return FileResponse("/tmp/report.pdf", as_attachment=True)
```

`None` превращается в `204 No Content`, mappings - в JSON, строки - в HTML,
bytes - в `application/octet-stream`.

## Схемы, модели и OpenAPI

Классы схем описывают данные один раз и переиспользуются рантайм-проекциями:

```python
from muscles import Column, Key, Model, String


class Document(Model):
    id = Column(Key)
    title = Column(String, required=True)
```

Тела запросов, тела ответов и параметры используются сборщиками OpenAPI в ASGI
и WSGI.

Подробнее: [schema.md](schema.md).

## Внедрение зависимостей

DI ядра строится на `Dependency`, `DependencyStorage` и `inject()`:

```python
from muscles import Dependency


class StoreInterface:
    pass


@Dependency.init(StoreInterface)
class Store(StoreInterface):
    pass
```

Рантаймы могут получать аннотированные зависимости из этого контейнера ядра при
вызове обработчиков.

Подробнее: [dependency.md](dependency.md).

## Конфигурация и режим выполнения

`Configurator` читает конфигурацию проекта. Помощники режима выполнения задают
поведение для разработки, тестов и продакшена.

Подробнее: [configure.md](configure.md).

## Действия (Actions)

Действия ядра (`Actions`) - контракты, не завязанные на конкретный протокол.
Их можно проецировать в HTTP, CLI, MCP, JSON-RPC, SSE и другие рантайм-слои
через `ActionDispatcher`.

Подробнее:

- [action-contract.en.md](action-contract.en.md)
- [action-contract.ru.md](action-contract.ru.md)

## Тестирование ядра из исходников

Из репозитория ядра:

```bash
PYTHONPATH=src python3 -m pytest
```

Для пакетов экосистемы из соседних локальных копий:

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-mcp/src:../muscles-sql/src:../muscles-otel/src:../muscles-documents/src:../muscles-ai/src:src python3 -m pytest
```

## Глубокие справочники

- Карта репозиториев:
  - [repositories.md](repositories.md)
- Документация рантаймов и расширений:
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
- [production-deploy.md](production-deploy.md)
- [roadmap-baseline.md](roadmap-baseline.md)
- [schema.md](schema.md)
- [value-objects-rules.md](value-objects-rules.md)
- [watchdog.md](watchdog.md)
