import pytest

from muscles.core import (
    ActionContext,
    ActionContract,
    ActionDispatcher,
    ActionNotFound,
    ActionPermissionDenied,
    ActionValidationError,
    ApplicationMeta,
    ApplicationRegistry,
    Context,
    BaseStrategy,
    get_application_registry,
    inspect_application,
    register_action,
)


class _EchoStrategy(BaseStrategy):
    def execute(self, *args, **kwargs):
        return kwargs


class _AppA(metaclass=ApplicationMeta):
    context = Context(_EchoStrategy)


class _AppB(metaclass=ApplicationMeta):
    context = Context(_EchoStrategy)


BOOKING_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "guest_count": {"type": "integer"},
    },
    "required": ["title"],
}


BOOKING_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
    },
}


def test_action_contract_registers_in_application_registry():
    app = _AppA()

    def create_booking(payload, context):
        return {"id": 1, "title": payload["title"], "transport": context.transport}

    contract = register_action(
        app,
        name="bookings.create",
        description="Create booking",
        input_schema=BOOKING_INPUT_SCHEMA,
        output_schema=BOOKING_OUTPUT_SCHEMA,
        rules=["bookings.public_create"],
        transports=["http", "mcp"],
        handler=create_booking,
        metadata={"stream": False},
    )

    registry = get_application_registry(app)
    assert isinstance(registry, ApplicationRegistry)
    assert registry.get_action("bookings.create") is contract
    assert registry.actions == [contract]


def test_app_action_decorator_registers_contract_and_handler():
    app = _AppA()

    @app.action(
        name="bookings.decorated",
        input_schema=BOOKING_INPUT_SCHEMA,
        output_schema=BOOKING_OUTPUT_SCHEMA,
        transports=["http"],
    )
    def create_booking(payload, context):
        return {"id": 7, "title": payload["title"]}

    result = ActionDispatcher(app).execute("bookings.decorated", {"title": "Call"}, transport="http")
    assert result.value == {"id": 7, "title": "Call"}


def test_inspect_application_returns_machine_readable_action_contract():
    app = _AppA()

    register_action(
        app,
        name="bookings.inspect",
        description="Inspect booking",
        input_schema=BOOKING_INPUT_SCHEMA,
        output_schema=BOOKING_OUTPUT_SCHEMA,
        rules=["bookings.public_create"],
        transports=["http", "cli", "mcp"],
        handler=lambda payload, context: payload,
    )

    contract = inspect_application(app)

    action = next(item for item in contract["actions"] if item["name"] == "bookings.inspect")
    assert action["description"] == "Inspect booking"
    assert action["input_schema"] == BOOKING_INPUT_SCHEMA
    assert action["output_schema"] == BOOKING_OUTPUT_SCHEMA
    assert action["rules"] == ["bookings.public_create"]
    assert action["transports"] == ["http", "cli", "mcp"]
    assert "handler" not in action
    assert action["handler_ref"].endswith(".<lambda>")


def test_action_dispatcher_validates_input_and_raises_core_error():
    app = _AppA()
    register_action(
        app,
        name="bookings.validate",
        input_schema=BOOKING_INPUT_SCHEMA,
        handler=lambda payload, context: payload,
    )

    with pytest.raises(ActionValidationError) as exc_info:
        ActionDispatcher(app).execute("bookings.validate", {"guest_count": 2}, transport="mcp")

    assert exc_info.value.action_name == "bookings.validate"
    assert "title" in exc_info.value.message


def test_action_dispatcher_checks_callable_rules_in_core():
    app = _AppA()

    def deny(payload, context):
        return False

    register_action(
        app,
        name="bookings.denied",
        input_schema=BOOKING_INPUT_SCHEMA,
        rules=[deny],
        handler=lambda payload, context: payload,
    )

    with pytest.raises(ActionPermissionDenied):
        ActionDispatcher(app).execute("bookings.denied", {"title": "Call"}, transport="mcp")


def test_action_dispatcher_normalizes_permission_error_from_rule():
    app = _AppA()

    def deny(payload, context):
        raise PermissionError("Denied by rule engine")

    register_action(
        app,
        name="bookings.rule_error",
        input_schema=BOOKING_INPUT_SCHEMA,
        rules=[deny],
        handler=lambda payload, context: payload,
    )

    with pytest.raises(ActionPermissionDenied) as exc_info:
        ActionDispatcher(app).execute("bookings.rule_error", {"title": "Call"}, transport="mcp")

    assert exc_info.value.message == "Denied by rule engine"


def test_action_dispatcher_calls_handler_with_action_context():
    app = _AppA()
    calls = []

    def create_booking(payload, context: ActionContext):
        calls.append((payload, context.action.name, context.transport))
        return {"id": 1, "title": payload["title"]}

    register_action(
        app,
        name="bookings.dispatch",
        input_schema=BOOKING_INPUT_SCHEMA,
        handler=create_booking,
    )

    result = ActionDispatcher(app).execute("bookings.dispatch", {"title": "HTTP"}, transport="http")

    assert result.action_name == "bookings.dispatch"
    assert result.transport == "http"
    assert result.value == {"id": 1, "title": "HTTP"}
    assert calls == [({"title": "HTTP"}, "bookings.dispatch", "http")]


def test_action_dispatcher_marks_iterable_handler_result_as_stream():
    app = _AppA()

    def stream_booking(payload, context):
        yield {"event": "progress", "title": payload["title"]}

    register_action(
        app,
        name="bookings.stream",
        input_schema=BOOKING_INPUT_SCHEMA,
        metadata={"stream": True},
        handler=stream_booking,
    )

    result = ActionDispatcher(app).execute("bookings.stream", {"title": "Live"}, transport="sse")

    assert result.is_stream is True
    assert list(result.value) == [{"event": "progress", "title": "Live"}]


def test_action_dispatcher_raises_core_not_found_error():
    app = _AppA()

    with pytest.raises(ActionNotFound):
        ActionDispatcher(app).execute("bookings.missing", {}, transport="mcp")


def test_action_registry_is_isolated_between_app_instances():
    app_a = _AppA()
    app_b = _AppB()

    register_action(app_a, name="bookings.a", handler=lambda payload, context: payload)
    register_action(app_b, name="bookings.b", handler=lambda payload, context: payload)

    assert get_application_registry(app_a).get_action("bookings.a").name == "bookings.a"
    assert get_application_registry(app_b).get_action("bookings.b").name == "bookings.b"
    with pytest.raises(ActionNotFound):
        ActionDispatcher(app_a).execute("bookings.b", {}, transport="mcp")


def test_action_contract_does_not_leak_sensitive_config():
    app = _AppA()
    app.config = type(
        "_Config",
        (),
        {"_object": {"secret": {"token": "hidden"}, "main": {"ENV": "development"}}},
    )()
    register_action(app, name="bookings.safe", handler=lambda payload, context: payload)

    contract = inspect_application(app)

    assert any(action["name"] == "bookings.safe" for action in contract["actions"])
    assert contract["config"]["known_keys"] == ["main.ENV", "secret.token"]
    assert contract["config"]["values"] == {}
