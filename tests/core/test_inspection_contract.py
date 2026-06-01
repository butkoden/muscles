from muscles.core import inspect_application


class _FakeStrategy:
    pass


class _FakeContext:
    strategy = _FakeStrategy


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
    context = _FakeContext()
    config = _FakeConfig()
    __muscles_routes__ = [_handler]


def test_inspection_contract_core_shape():
    contract = inspect_application(_FakeApp())

    assert contract["contract_version"] == "1"
    assert contract["framework"] == "Muscles"
    assert contract["runtime_mode"] == "development"
    assert contract["app"] == "_FakeApp"
    assert contract["strategies"] == ["fake"]
    assert len(contract["routes"]) == 1
    assert contract["routes"][0]["path"] == "/api/v1/bookings"


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
