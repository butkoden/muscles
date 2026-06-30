import asyncio
from dataclasses import dataclass

import pytest

from muscles.core import ApplicationException, BackendPipeline, Dependency, cors


class Request:
    def __init__(self, handler, body=None, path="/api/documents", method="POST"):
        self.route = {"handler": handler}
        self.itinerary = None
        self.path = path
        self.method = method
        self.content_type = "application/json"
        self.headers = {}
        self.cookies = {}
        self.query = {}
        self.json = body if body is not None else {}


@dataclass
class CreateDocument:
    title: str


class StoreInterface:
    pass


@Dependency.init(StoreInterface)
class Store(StoreInterface):
    name = "documents"


class RejectingSecurity:
    def authenticate_header(self, value):
        return None


class Itinerary:
    def __init__(self):
        self.middlewares = []
        self.guards = []

    def get_middlewares(self):
        return list(self.middlewares)

    def get_guards(self, request):
        return list(self.guards)

    def is_auth_disabled(self, route):
        return getattr(route["handler"], "auth", None) is False


def test_pipeline_builds_typed_body_and_injects_dependency():
    pipeline = BackendPipeline()

    def handler(body: CreateDocument, store: StoreInterface):
        return {"title": body.title, "store": store.name}

    result = pipeline.call_handler(Request(handler, {"title": "Spec"}), {})

    assert result == {"title": "Spec", "store": "documents"}


def test_pipeline_uses_query_header_cookie_fallbacks():
    pipeline = BackendPipeline()

    def handler(page, trace_id, session):
        return page, trace_id, session

    request = Request(handler, {})
    request.query = {"page": "2"}
    request.headers = {"Trace-Id": "abc"}
    request.cookies = {"session": "cookie"}

    result = pipeline.call_handler(request, {})

    assert result == ("2", "abc", "cookie")


def test_pipeline_missing_required_argument_returns_validation_error():
    pipeline = BackendPipeline()

    def handler(required):
        return required

    with pytest.raises(ApplicationException) as exc:
        pipeline.call_handler(Request(handler, {}), {})

    assert exc.value.status == 422


def test_pipeline_auth_false_skips_matching_guards_and_security():
    pipeline = BackendPipeline()
    itinerary = Itinerary()
    itinerary.guards.append(lambda request: ({"error": "unauthorized"}, 401))

    def handler(request):
        return "ok"

    handler.auth = False
    handler.security = [RejectingSecurity()]
    request = Request(handler, path="/api/login")
    request.itinerary = itinerary

    assert pipeline.run_guards(request) is None
    pipeline.run_security(request)


def test_pipeline_runs_middleware_stack():
    pipeline = BackendPipeline()
    itinerary = Itinerary()
    calls = []

    def audit(request, call_next):
        calls.append("before")
        response = call_next(request)
        calls.append("after")
        return response

    itinerary.middlewares.append(audit)

    def handler(request):
        calls.append("handler")
        return {"ok": True}

    request = Request(handler)
    request.itinerary = itinerary

    assert pipeline.call_route_handler(request, {}) == {"ok": True}
    assert calls == ["before", "handler", "after"]


def test_pipeline_supports_async_handlers_and_guards():
    pipeline = BackendPipeline()
    itinerary = Itinerary()

    async def guard(request):
        return None

    async def handler(request):
        return {"ok": True}

    itinerary.guards.append(guard)
    request = Request(handler)
    request.itinerary = itinerary

    assert asyncio.run(pipeline.run_guards_async(request)) is None
    assert asyncio.run(pipeline.call_route_handler_async(request, {})) == {"ok": True}


def test_pipeline_applies_cors_middleware_to_core_response():
    pipeline = BackendPipeline()
    itinerary = Itinerary()
    itinerary.middlewares.append(cors(allow_origins=["https://app.example"], allow_methods=["GET"]))

    def handler(request):
        return {"ok": True}

    request = Request(handler, method="GET")
    request.origin = "https://app.example"
    request.itinerary = itinerary

    response = pipeline.call_route_handler(request, {})

    assert response.headers["Access-Control-Allow-Origin"] == "https://app.example"
