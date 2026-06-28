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

## Справочник по репозиториям экосистемы

Ядро намеренно хранит контракты, не завязанные на конкретный протокол.
Репозитории рантаймов, протоколов и интеграций расширяют эти контракты.
Используйте таблицы ниже как быстрый справочник, когда нужно понять, где должно
жить поведение.

### Рантаймы и протокольные расширения

| Репозиторий | Для чего служит | Когда использовать |
| --- | --- | --- |
| [`muscles-asgi`](https://github.com/butkoden/muscles-asgi) | ASGI-рантайм поверх маршрутизации и схем ядра. | Асинхронные HTTP-приложения, REST API, OpenAPI/Swagger UI, типизированный вызов обработчиков, загрузки файлов, CORS preflight и ASGI `TestClient`. |
| [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) | WSGI-рантайм поверх маршрутизации и схем ядра. | Классические WSGI-приложения, страницы и шаблоны, статические файлы, REST API, OpenAPI/Swagger UI, загрузки файлов и CORS preflight. |
| [`muscles-cli`](https://github.com/butkoden/muscles-cli) | CLI-проекция той же модели приложения. | Маршрутизация команд и групп, локальные инструменты разработчика и генерация структуры проекта по golden path. |
| [`muscles-jsonrpc`](https://github.com/butkoden/muscles-jsonrpc) | JSON-RPC-проекция. | Публикация действий ядра и контрактов приложения как JSON-RPC-методов. |
| [`muscles-sse`](https://github.com/butkoden/muscles-sse) | Проекция Server-Sent Events. | Потоковая доставка результатов действий через SSE. |
| [`muscles-mcp`](https://github.com/butkoden/muscles-mcp) | MCP-проекция. | Публикация действий приложения как MCP-инструментов. |

### Данные, наблюдаемость и интеграции

| Репозиторий | Для чего служит | Когда использовать |
| --- | --- | --- |
| [`muscles-sql`](https://github.com/butkoden/muscles-sql) | SQL-расширение для хранения данных. | Интеграция с базами данных и паттерны хранения, которые не должны жить внутри протокольных рантаймов. |
| [`muscles-otel`](https://github.com/butkoden/muscles-otel) | Расширение для наблюдаемости. | Инструментация в стиле OpenTelemetry, трассировки и метрики вокруг ядра и рантаймов. |

### Примеры, совместимость и поддерживающие репозитории

| Репозиторий | Для чего служит | Когда использовать |
| --- | --- | --- |
| [`muscular-example`](https://github.com/butkoden/muscular-example) | Пример приложения. | Посмотреть, как ядро, рантаймы и расширения собираются в одно приложение. |
| [`muscles-benchmarks`](https://github.com/butkoden/muscles-benchmarks) | Рабочая область для бенчмарков. | Измерение производительности маршрутизации, DI и изменений в рантаймах. |
| [`muscles-landing`](https://github.com/butkoden/muscles-landing) | Публичный сайт документации и продукта. | Продуктовая документация и сайт проекта. |
| [`muscular-asgi`](https://github.com/butkoden/muscular-asgi) | Устаревший ASGI-пакет для совместимости. | Исторические проверки совместимости, пока экосистема сходится на `muscles-asgi`. |

Когда добавляется новая функция ядра, здесь нужно описывать независимый от
протокола контракт, а примеры для конкретного рантайма добавлять в репозиторий
расширения, который этот контракт исполняет.

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
PYTHONPATH=../muscles/src:src python3 -m pytest
```

## Глубокие справочники

- Документация рантайм-репозиториев:
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
