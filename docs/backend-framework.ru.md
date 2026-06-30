# Backend-примитивы фреймворка

Язык: русский  
Английская версия: [backend-framework.md](backend-framework.md)

Ядро Muscles содержит общие backend-примитивы, которые используют ASGI и WSGI.
Идея в том, чтобы метаданные маршрутов, правила безопасности и контракты
ответов жили в одном месте, а не в правках, привязанных к конкретному
транспорту.

Реализации рантаймов:

- [`muscles-asgi`](https://github.com/butkoden/muscles-asgi) исполняет эти
  примитивы в ASGI: типизированные аргументы обработчиков, `guards`, правила
  безопасности, CORS preflight, OpenAPI-проекцию и `TestClient`.
- [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) исполняет те же
  примитивы в WSGI: типизированные аргументы обработчиков, `guards`, правила
  безопасности, CORS preflight и OpenAPI-проекцию.

## Backend Pipeline

`BackendPipeline` - общий runtime-контракт обработки запроса. Runtime-адаптеры
передают в него framework request и параметры найденного маршрута, а pipeline
выполняет:

- сбор типизированных аргументов handler из path params, body, query, headers и cookies;
- разрешение зависимостей;
- route guards и переопределение `auth=False`;
- route-level security providers;
- middleware, включая CORS middleware.

Транспорты по-прежнему отвечают за разбор протокола и сериализацию ответа. Так
поведение ASGI и WSGI остается одинаковым без копирования handler-логики в
каждом runtime.

## Dependency Container

`DependencyContainer` - небольшой контейнер зависимостей со scope уровня
приложения и запроса:

```python
from muscles import DependencyContainer

container = DependencyContainer()
container.register(StoreInterface, SqliteStore, scope="app")
request_scope = container.create_scope()

store = request_scope.resolve(StoreInterface)
```

Поддерживаются scope `app`, `request` и `transient`. Существующие регистрации
через `Dependency(...)` остаются для совместимости; runtime можно постепенно
переводить на явные контейнеры.

## Группы маршрутов

`group()` добавляет общий префикс и метаданные для набора маршрутов:

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

Метаданные группы наследуются зарегистрированными обработчиками. Сборщики
OpenAPI в ASGI и WSGI используют их для `tags`, `security` и общих `responses`.

Маршруты на одном path могут иметь разные ключи для разных HTTP-методов:

```python
@api.init("/api/documents", key="documents.list", method="get")
def list_documents(request):
    return {"items": []}


@api.init("/api/documents", key="documents.create", method="post")
def create_document(request):
    return {"created": True}
```

Core itinerary хранит все route records на найденном terminal node и затем
выбирает обработчик по method и content type.

Для переопределения авторизации на конкретном endpoint используйте `auth`:

```python
api = Itinerary(name="api")
jwt_auth = BearerAuthSecurity()
api_routes = api.group("/api", security=[jwt_auth], response={401: "Unauthorized"})


@api_routes.init("/login", method="post", auth=False)
def login(request):
    return {"token": "issued-token"}


@api_routes.init("/service-token", method="post", auth=["ApiKey"])
def service_token(request):
    return {"ok": True}
```

`auth=False` делает endpoint публичным: для этого маршрута пропускаются
подходящие `guards` и унаследованные метаданные `security`. `auth=[...]`
заменяет унаследованную схему безопасности на конкретном endpoint.
Используйте `guard(..., except_=...)` для исключений по пути, а `auth=False` -
когда исключение принадлежит самому маршруту.

## Middleware и guards

`use()` регистрирует middleware. Middleware получает `(request, call_next)` и
возвращает ответ:

```python
def audit_middleware(request, call_next):
    response = call_next(request)
    return response


api.use(audit_middleware)
```

`guard()` регистрирует проверку маршрута по шаблону пути. `/**` совпадает с
вложенными путями:

```python
def require_auth(request):
    if request.user.is_guest():
        return {"error": "unauthorized"}, 401


api.guard("/api/**", require_auth, except_=["/api/public/**"])
```

Для отдельных публичных endpoint внутри защищённого API лучше использовать
метаданные маршрута:

```python
@api.init("/api/login", method="post", auth=False)
def login(request):
    return {"token": "issued-token"}
```

Рантайм-репозитории выполняют `guards` до вызова прикладного обработчика.

## Сопоставление исключений

`map_error()` связывает доменные исключения с HTTP-статусами и
необязательными пользовательскими обработчиками:

```python
class WorkspaceAccessDenied(Exception):
    pass


api.map_error(WorkspaceAccessDenied, status=404)
api.map_error(ValueError, status=422)
```

Когда ASGI- или WSGI-обработчик выбрасывает сопоставленное исключение, рантайм
сохраняет назначенный статус до создания ответа об ошибке.

## Bearer JWT-аутентификация

`BearerAuthSecurity` описывает HTTP bearer-аутентификацию в OpenAPI.
`BearerJwtAuth` добавляет небольшой HS256 JWT-провайдер:

```python
from muscles import BearerJwtAuth

jwt_auth = BearerJwtAuth(secret=settings.jwt_secret, subject="sub")
token = jwt_auth.issue({"sub": "user-1"})
auth_result = jwt_auth.authenticate_header(f"Bearer Bearer {token}")

assert auth_result["payload"]["sub"] == "user-1"
assert auth_result["user"].uid == "user-1"
```

`authenticate_header()` принимает дублирующийся bearer-префикс для
совместимости с legacy-клиентами и возвращает
`{"payload": ..., "token": ..., "user": ...}`.

## Ответы

Помощники ответов ядра нормализуются всеми рантаймами:

```python
from muscles import BytesResponse, FileResponse, JsonResponse, NoContentResponse

return JsonResponse({"ok": True})
return NoContentResponse()
return BytesResponse(b"PNG", content_type="image/png")
return FileResponse("/tmp/report.pdf", as_attachment=True)
```

`None` нормализуется в `204 No Content`, mappings - в JSON, строки - в HTML,
bytes - в `application/octet-stream`.

## CORS

`cors()` используется как middleware маршрута:

```python
from muscles import cors

api.use(cors(
    allow_origins=["https://app.example"],
    allow_credentials=True,
))
```

ASGI и WSGI используют один middleware для обычных ответов и `OPTIONS`
preflight-ответов.
