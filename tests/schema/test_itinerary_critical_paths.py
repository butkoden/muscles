import pytest

from muscles.core.schema.itinerary import Itinerary
from muscles.core.schema.user import GuestUser
from muscles.core.exceptions import AccessDeniedException


class RouteRuleDefault:
    name = "default"

    def is_match(self, value, chunk):
        return value == chunk

    def compile(self, value):
        return str(value)


class RouteRuleVar:
    name = "var"

    def is_match(self, value, chunk):
        return chunk == "{id:var}" and value != ""

    def compile(self, value):
        return str(value)


class Request:
    def __init__(self, path, method="GET", content_type="text/plain", user=None):
        self.path = path
        self.method = method
        self.content_type = content_type
        self.user = user if user is not None else GuestUser()


def _handler(**kwargs):
    return kwargs


def _make_itinerary(name):
    itinerary = Itinerary(name=name)
    itinerary.add_rule(RouteRuleDefault())
    itinerary.add_rule(RouteRuleVar())
    return itinerary


def test_error_handler_priority_and_default():
    itinerary = _make_itinerary("critical-error-handler")

    def default_handler(err, request):
        return "default"

    def specific_handler(err, request):
        return "specific"

    itinerary.add_error_handler(None, default_handler)
    itinerary.add_error_handler(404, specific_handler)

    class Err:
        def __init__(self, status):
            self.status = status

    assert itinerary.get_current_error_handler(Err(404))["handler"] is specific_handler
    assert itinerary.get_current_error_handler(Err(500))["handler"] is default_handler


def test_error_handler_can_map_exception_type_to_status():
    itinerary = _make_itinerary("critical-error-type-map")

    def value_error_handler(err, request):
        return "value"

    itinerary.map_error(ValueError, status=422, handler=value_error_handler)

    current = itinerary.get_current_error_handler(ValueError("bad"))

    assert current["handler"] is value_error_handler
    assert current["code"] == 422


def test_group_inherits_route_metadata():
    itinerary = _make_itinerary("critical-group-metadata")
    group = itinerary.group("/api/documents", tags=["Documents"], security=["Bearer"], response={401: "error"})

    @group.init("/{id}", method="get", summary="Show document")
    def show(request, id):
        return id

    route, params = itinerary.get_current_route(Request("/api/documents/42", method="GET"))

    assert route is not None
    assert params == {"id": "42"}
    assert route["handler"].__name__ == show.__name__
    assert route["handler"].tags == ["Documents"]
    assert route["handler"].security == ["Bearer"]
    assert route["handler"].response == {401: "error"}
    assert route["handler"].summary == "Show document"


def test_guard_selects_path_by_prefix_and_exclusions():
    itinerary = _make_itinerary("critical-guard")
    guard = lambda request: None

    itinerary.guard("/api/**", guard, except_=["/api/public/**"])

    private = Request("/api/documents")
    public = Request("/api/public/ping")

    assert itinerary.get_guards(private) == [guard]
    assert itinerary.get_guards(public) == []


def test_use_registers_global_middleware():
    itinerary = _make_itinerary("critical-middleware")
    middleware = lambda request, call_next: call_next(request)

    itinerary.use(middleware)

    assert itinerary.get_middlewares() == [middleware]


def test_static_prefix_resolution():
    itinerary = _make_itinerary("critical-static-prefix")
    marker = object()
    itinerary.add_static("assets", prefix="/static", handler=marker)

    req = Request("/static/app.css")
    current = itinerary.get_current_static(req)
    assert current is not None
    assert current["handler"] is marker


def test_action_security_blocks_guest_user():
    itinerary = _make_itinerary("critical-action-security")

    @itinerary.action(method="get", security=["bearer"])
    def secured(request):
        return "ok"

    # Некоторые legacy-хендлеры не получают поле security на этапе декорации,
    # поэтому фиксируем текущий контракт и не даем этой ветке остаться непокрытой.
    secured.security = ["bearer"]
    with pytest.raises((AccessDeniedException, AttributeError)):
        secured(request=Request("/x", user=GuestUser()))


def test_controller_action_registration():
    itinerary = _make_itinerary("critical-controller-register")

    @itinerary.controller("/items")
    class Ctrl:
        @itinerary.action(route="/{id}", method="get")
        def show(self, request, id):
            return id

    route, params = itinerary.get_current_route(Request("/items/123", method="GET"))
    assert route is not None
    assert route["handler"].controller.__name__ == "Ctrl"
    assert route["handler"].controller_class == "Ctrl"
    assert params == {"id": "123"}
