# Backend Framework Primitives

Язык: русский  
English version: [backend-framework.md](backend-framework.md)

Muscles core содержит общие backend primitives, которые используют ASGI и WSGI
runtimes. Идея в том, чтобы route metadata, security и response contracts жили
в одном месте, а не в transport-specific monkey patches.

Runtime implementations:

- [`muscles-asgi`](https://github.com/butkoden/muscles-asgi) исполняет эти
  primitives в ASGI: typed handler arguments, guards, security, CORS preflight,
  OpenAPI projection и `TestClient`.
- [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) исполняет те же
  primitives в WSGI: typed handler arguments, guards, security, CORS preflight
  и OpenAPI projection.

## Route Groups

`group()` добавляет общий prefix и metadata для набора routes:

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

Metadata группы наследуется зарегистрированными handlers. ASGI и WSGI OpenAPI
builders используют её для tags, security и common responses.

## Middleware And Guards

`use()` регистрирует middleware. Middleware получает `(request, call_next)` и
возвращает response:

```python
def audit_middleware(request, call_next):
    response = call_next(request)
    return response


api.use(audit_middleware)
```

`guard()` регистрирует route guard по path pattern. `/**` матчится на вложенные
paths:

```python
def require_auth(request):
    if request.user.is_guest():
        return {"error": "unauthorized"}, 401


api.guard("/api/**", require_auth, except_=["/api/public/**"])
```

Runtime-репозитории выполняют guards до вызова business handler.

## Exception Mapping

`map_error()` связывает domain exceptions с HTTP status codes и optional custom
handlers:

```python
class WorkspaceAccessDenied(Exception):
    pass


api.map_error(WorkspaceAccessDenied, status=404)
api.map_error(ValueError, status=422)
```

Когда ASGI или WSGI handler выбрасывает mapped exception, runtime сохраняет
mapped status до создания problem response.

## Bearer JWT Auth

`BearerAuthSecurity` описывает HTTP bearer auth в OpenAPI. `BearerJwtAuth`
добавляет небольшой HS256 JWT provider:

```python
from muscles import BearerJwtAuth

jwt_auth = BearerJwtAuth(secret=settings.jwt_secret, subject="sub")
token = jwt_auth.issue({"sub": "user-1"})
auth_result = jwt_auth.authenticate_header(f"Bearer Bearer {token}")

assert auth_result["payload"]["sub"] == "user-1"
assert auth_result["user"].uid == "user-1"
```

`authenticate_header()` принимает дублирующийся bearer prefix для совместимости
с legacy clients и возвращает `{"payload": ..., "token": ..., "user": ...}`.

## Responses

Core response helpers нормализуются всеми runtimes:

```python
from muscles import BytesResponse, FileResponse, JsonResponse, NoContentResponse

return JsonResponse({"ok": True})
return NoContentResponse()
return BytesResponse(b"PNG", content_type="image/png")
return FileResponse("/tmp/report.pdf", as_attachment=True)
```

`None` нормализуется в `204 No Content`, mappings - в JSON, strings - в HTML,
bytes - в `application/octet-stream`.

## CORS

`cors()` используется как route middleware:

```python
from muscles import cors

api.use(cors(
    allow_origins=["https://app.example"],
    allow_credentials=True,
))
```

ASGI и WSGI runtimes используют один middleware для обычных responses и
`OPTIONS` preflight responses.
