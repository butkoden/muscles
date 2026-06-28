# Backend Framework Primitives

Muscles core provides shared backend primitives used by ASGI and WSGI runtimes.
The goal is to keep route metadata, security and response contracts in one
place instead of patching each transport separately.

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
