from muscles.core import (
    ApplicationMeta,
    ApplicationRegistry,
    Context,
    BaseStrategy,
    get_application_registry,
    inspect_application,
)


class _EchoStrategy(BaseStrategy):
    def execute(self, *args, **kwargs):
        return kwargs.get("value")


class _RouteNode:
    def __init__(self, key, full_route):
        self.key = key
        self.full_route = full_route


class _RouteHandler:
    def __init__(self, key, full_route, method="get", actions=None):
        self.node = _RouteNode(key, full_route)
        self.method = method
        self.actions = actions or []
        self.__name__ = f"{key}_handler"
        self.__module__ = "tests.fake"


class _AppA(metaclass=ApplicationMeta):
    context = Context(_EchoStrategy, params={"value": "a"})


class _AppB(metaclass=ApplicationMeta):
    context = Context(_EchoStrategy, params={"value": "b"})


def test_application_registry_is_scoped_per_app_instance():
    app_a = _AppA()
    app_b = _AppB()

    reg_a = get_application_registry(app_a)
    reg_b = get_application_registry(app_b)
    assert isinstance(reg_a, ApplicationRegistry)
    assert isinstance(reg_b, ApplicationRegistry)
    assert reg_a is not reg_b

    reg_a.add_route(_RouteHandler("a-route", "/a"))
    reg_b.add_route(_RouteHandler("b-route", "/b"))

    routes_a = inspect_application(app_a)["routes"]
    routes_b = inspect_application(app_b)["routes"]
    assert routes_a[0]["path"] == "/a"
    assert routes_b[0]["path"] == "/b"


def test_registry_events_do_not_leak_between_apps():
    app_a = _AppA()
    app_b = _AppB()
    reg_a = get_application_registry(app_a)
    reg_b = get_application_registry(app_b)

    reg_a.emit_event("lifecycle", {"name": "boot_a"})
    reg_b.emit_event("lifecycle", {"name": "boot_b"})

    assert reg_a.get_events("lifecycle") == [{"name": "boot_a"}]
    assert reg_b.get_events("lifecycle") == [{"name": "boot_b"}]
