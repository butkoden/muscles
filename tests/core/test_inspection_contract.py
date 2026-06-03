from muscles.core import Context, inspect_application


class _FakeStrategy:
    pass


class _FakeContext:
    pass


class _FakeCliContext(_FakeContext):
    pass


class _FakeConfig:
    _object = {
        "main": {"ENV": "development"},
        "database": {"url": "sqlite:///db.sqlite3"},
        "secret": {"token": "hidden"},
    }

    def get(self, path, default=None):
        if path == "main.ENV":
            return "development"
        return default


class _FakeRouteNode:
    key = "api.v1.bookings.create"
    full_route = "/api/v1/bookings"
    method = "post"


def _handler():
    return True


_handler.node = _FakeRouteNode()
_handler.method = "post"


class _FakeApp:
    context = Context(_FakeStrategy, transport="asgi")
    secondary = Context(_FakeStrategy, transport=context)
    cli = Context(_FakeStrategy, transport="cli")
    config = _FakeConfig()
    __muscles_routes__ = [_handler]


def test_inspection_contract_core_shape():
    contract = inspect_application(_FakeApp())

    assert contract["contract_version"] == "1"
    assert contract["framework"] == "Muscles"
    assert contract["runtime_mode"] == "development"
    assert contract["app"] == "_FakeApp"
    assert {item["name"] for item in contract["contexts"]} == {"context", "secondary", "cli"}
    assert any(item["name"] == "secondary" and item["transport"] == "context" for item in contract["contexts"])
    assert any(item["name"] == "context" and item["strategy"] == "_FakeStrategy" for item in contract["contexts"])
    assert any(item["name"] == "cli" for item in contract["contexts"])
    assert len(contract["routes"]) == 1
    assert contract["routes"][0]["path"] == "/api/v1/bookings"
    assert "route_contract" in contract
    assert contract["route_contract"]["canonical"]["openapi"] == "/openapi.json"
    assert contract["route_contract"]["aliases"]["schema"] == "/openapi.json"
    assert contract["routes"][0]["canonical"] == _FakeRouteNode.full_route
    assert set(contract["routes"][0]["aliases"]) == set()


def test_inspection_contract_hides_sensitive_config_values():
    contract = inspect_application(_FakeApp())
    config = contract["config"]

    assert "database.url" in config["known_keys"]
    assert "secret.token" in config["known_keys"]
    assert config["values"] == {}


def test_inspection_contract_allows_sensitive_values_when_requested():
    contract = inspect_application(_FakeApp(), include_sensitive=True)
    assert contract["config"]["values"]["database.url"] == "sqlite:///db.sqlite3"
    assert contract["config"]["values"]["secret.token"] == "hidden"
