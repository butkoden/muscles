# Backend Framework Primitives

Language: English  
Russian version: [backend-framework.ru.md](backend-framework.ru.md)

Muscles core provides shared backend primitives used by ASGI and WSGI runtimes.
The goal is to keep route metadata, security and response contracts in one
place instead of patching each transport separately.

Runtime implementations:

- [`muscles-asgi`](https://github.com/butkoden/muscles-asgi) executes these
  primitives in ASGI, including typed handler arguments, guards, security,
  CORS preflight, OpenAPI projection and `TestClient`.
- [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) executes the same
  primitives in WSGI, including typed handler arguments, guards, security,
  CORS preflight and OpenAPI projection.

## Backend Pipeline

`BackendPipeline` is the shared runtime contract for request handling. Runtime
adapters pass a framework request and matched route params into the pipeline,
and the pipeline handles:

- typed handler argument binding from path params, body, query, headers and cookies;
- dependency resolution;
- route guards and `auth=False` overrides;
- route-level security providers;
- middleware execution, including CORS middleware.

Transports still own protocol parsing and protocol response serialization. This
keeps ASGI and WSGI behavior aligned without copying handler logic into each
runtime.

## Dependency Container

`DependencyContainer` is a small app/request scoped container for framework
integrations:

```python
from muscles import DependencyContainer

container = DependencyContainer()
container.register(StoreInterface, SqliteStore, scope="app")
request_scope = container.create_scope()

store = request_scope.resolve(StoreInterface)
```

Supported scopes are `app`, `request` and `transient`. Existing
`Dependency(...)` registrations remain supported for compatibility; runtimes can
gradually move to explicit containers.

## Route Groups

Use `group()` to add a common prefix and metadata to a set of routes:

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

Group metadata is inherited by registered handlers. ASGI and WSGI OpenAPI
builders use this metadata for tags, security and common responses.

Routes on the same path can use distinct keys per HTTP method:

```python
@api.init("/api/documents", key="documents.list", method="get")
def list_documents(request):
    return {"items": []}


@api.init("/api/documents", key="documents.create", method="post")
def create_document(request):
    return {"created": True}
```

The core itinerary keeps all route records on the matched terminal node and then
selects by method and content type.

Use endpoint-level `auth` to override inherited auth metadata:

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

`auth=False` makes the endpoint public: matching guards and inherited security
metadata are skipped for that route. `auth=[...]` replaces inherited security on
that endpoint. Use `guard(..., except_=...)` for path-level exclusions, and
`auth=False` when the route itself owns the override.

## Middleware And Guards

`use()` registers middleware. A middleware receives `(request, call_next)` and
returns a response:

```python
def audit_middleware(request, call_next):
    response = call_next(request)
    return response


api.use(audit_middleware)
```

`guard()` registers a route guard by path pattern. `/**` matches nested paths:

```python
def require_auth(request):
    if request.user.is_guest():
        return {"error": "unauthorized"}, 401


api.guard("/api/**", require_auth, except_=["/api/public/**"])
```

For single public endpoints inside a protected API, prefer endpoint metadata:

```python
@api.init("/api/login", method="post", auth=False)
def login(request):
    return {"token": "issued-token"}
```

## Exception Mapping

`map_error()` maps domain exceptions to HTTP status codes and optional custom
handlers:

```python
class WorkspaceAccessDenied(Exception):
    pass


api.map_error(WorkspaceAccessDenied, status=404)
api.map_error(ValueError, status=422)
```

When ASGI or WSGI handlers raise a mapped exception, the runtime preserves the
mapped status before creating the problem response.

## Bearer JWT Auth

`BearerAuthSecurity` describes HTTP bearer auth in OpenAPI. `BearerJwtAuth`
adds a small HS256 JWT provider:

```python
from muscles import BearerJwtAuth

jwt_auth = BearerJwtAuth(secret=settings.jwt_secret, subject="sub")
token = jwt_auth.issue({"sub": "user-1"})
auth_result = jwt_auth.authenticate_header(f"Bearer Bearer {token}")
```

`authenticate_header()` accepts duplicate bearer prefixes for compatibility with
legacy clients and returns `{"payload": ..., "token": ..., "user": ...}`. The
returned user has `uid` set from the configured JWT subject claim.

## Responses

Core response helpers are normalized by all runtimes:

```python
from muscles import BytesResponse, FileResponse, JsonResponse, NoContentResponse

return JsonResponse({"ok": True})
return NoContentResponse()
return BytesResponse(b"PNG", content_type="image/png")
return FileResponse("/tmp/report.pdf", as_attachment=True)
```

`None` is normalized to `204 No Content`, mappings to JSON, strings to HTML and
bytes to `application/octet-stream`.

## CORS

Use `cors()` as route middleware:

```python
from muscles import cors

api.use(cors(
    allow_origins=["https://app.example"],
    allow_credentials=True,
))
```

ASGI and WSGI runtimes use the same middleware for normal responses and
`OPTIONS` preflight responses.
