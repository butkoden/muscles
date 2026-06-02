from __future__ import annotations

import inspect
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Callable

from jsonschema import ValidationError, validate

from .registry import get_application_registry
from ..schema.pydantic_bridge import to_json_schema


class ActionError(Exception):
    code = "action_error"

    def __init__(self, action_name: str, message: str, data: Any = None):
        super().__init__(message)
        self.action_name = action_name
        self.message = message
        self.data = data


class ActionNotFound(ActionError):
    code = "action_not_found"


class ActionValidationError(ActionError):
    code = "action_validation_error"


class ActionPermissionDenied(ActionError):
    code = "action_permission_denied"


class ActionExecutionError(ActionError):
    code = "action_execution_error"


@dataclass(frozen=True)
class ActionContext:
    application: Any
    registry: Any
    action: "ActionContract"
    transport: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    action_name: str
    value: Any
    transport: str | None = None
    is_stream: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_contract(self) -> dict[str, Any]:
        return {
            "action_name": self.action_name,
            "value": self.value,
            "transport": self.transport,
            "is_stream": self.is_stream,
            "metadata": dict(self.metadata),
        }


STREAM_EVENT_TYPES = {"progress", "log", "result", "error"}


@dataclass(frozen=True)
class StreamEvent:
    type: str
    data: Any
    event_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.type not in STREAM_EVENT_TYPES:
            raise ValueError(f"Unknown stream event type: {self.type}")

    def to_contract(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "event_id": self.event_id,
            "metadata": dict(self.metadata),
        }


@dataclass
class StreamResult:
    source: Iterable[StreamEvent | dict[str, Any]]
    close: Callable[[], None] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __iter__(self):
        return iter(self.source)

    def close_source(self) -> None:
        if self.close is not None:
            self.close()
            return
        close = getattr(self.source, "close", None)
        if callable(close):
            close()


@dataclass
class ActionContract:
    name: str
    description: str = ""
    input_schema: Any = field(default_factory=lambda: {"type": "object", "properties": {}})
    output_schema: Any = field(default_factory=lambda: {"type": "object", "properties": {}})
    raw_input_schema: Any | None = field(default=None, repr=False, init=False)
    raw_output_schema: Any | None = field(default=None, repr=False, init=False)
    rules: list[Any] = field(default_factory=list)
    handler_ref: str | None = None
    transports: list[str] = field(default_factory=list)
    stream_output: bool = False
    stream_metadata: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    handler: Callable[..., Any] | None = None

    def __post_init__(self):
        self.raw_input_schema = self.input_schema
        self.raw_output_schema = self.output_schema
        self.input_schema = normalize_schema(self.input_schema)
        self.output_schema = normalize_schema(self.output_schema)
        if self.handler_ref is None and self.handler is not None:
            self.handler_ref = _handler_ref(self.handler)

    def to_contract(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "rules": [_rule_contract(rule) for rule in self.rules],
            "handler_ref": self.handler_ref,
            "transports": list(self.transports),
            "stream_output": self.stream_output,
            "stream": {
                "enabled": self.stream_output,
                "event_types": list(self.stream_metadata.get("event_types", sorted(STREAM_EVENT_TYPES))),
                "cooperative_cancellation": True,
                "backpressure": self.stream_metadata.get("backpressure", "transport-bounded"),
                "metadata": dict(self.stream_metadata),
            },
            "metadata": dict(self.metadata),
        }


@dataclass
class ApplicationContract:
    contract_version: str = "1"
    framework: str = "Muscles"
    app: str | None = None
    runtime_mode: str | None = None
    contexts: list[dict[str, Any]] = field(default_factory=list)
    routes: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    schemas: list[Any] = field(default_factory=list)
    rules: list[Any] = field(default_factory=list)
    cli: list[Any] = field(default_factory=list)
    sql: list[Any] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    def to_contract(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "framework": self.framework,
            "app": self.app,
            "runtime_mode": self.runtime_mode,
            "contexts": list(self.contexts),
            "routes": list(self.routes),
            "actions": list(self.actions),
            "schemas": list(self.schemas),
            "rules": list(self.rules),
            "cli": list(self.cli),
            "sql": list(self.sql),
            "config": dict(self.config),
        }


def normalize_schema(schema: Any) -> dict[str, Any]:
    if schema is None:
        return {"type": "object", "properties": {}}
    if isinstance(schema, dict):
        return schema
    if isinstance(schema, type) or hasattr(schema, "columns"):
        dumped = to_json_schema(schema)
        if isinstance(schema, type):
            name = schema.__name__
        else:
            name = schema.__class__.__name__
        return dumped.get(name, dumped)
    if hasattr(schema, "dump"):
        dumped = schema.dump()
        if isinstance(dumped, dict):
            return dumped
    return {"type": "object", "properties": {}}


def register_action(
    app,
    *,
    name: str,
    description: str = "",
    input_schema: Any = None,
    output_schema: Any = None,
    rules: list[Any] | None = None,
    handler_ref: str | None = None,
    transports: list[str] | None = None,
    stream_output: bool = False,
    stream_metadata: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    handler: Callable[..., Any] | None = None,
) -> ActionContract:
    contract = ActionContract(
        name=name,
        description=description,
        input_schema=input_schema,
        output_schema=output_schema,
        rules=list(rules or []),
        handler_ref=handler_ref,
        transports=list(transports or []),
        stream_output=stream_output,
        stream_metadata=dict(stream_metadata or {}),
        metadata=dict(metadata or {}),
        handler=handler,
    )
    get_application_registry(app).add_action(contract)
    return contract


def action(app, **options):
    def decorator(func):
        register_action(app, handler=func, **options)
        return func

    return decorator


def dispatch_action(app, action_name: str, payload: dict[str, Any] | None = None, transport: str | None = None, **kwargs):
    return ActionDispatcher(app).execute(action_name, payload=payload, transport=transport, **kwargs)


class ActionDispatcher:
    def __init__(self, app):
        self.app = app
        self.registry = get_application_registry(app)

    def execute(
        self,
        action_name: str,
        payload: dict[str, Any] | None = None,
        transport: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ActionResult:
        payload = payload or {}
        action = self.registry.get_action(action_name)
        if action is None:
            raise ActionNotFound(action_name, f"Action not found: {action_name}")
        context = ActionContext(
            application=self.app,
            registry=self.registry,
            action=action,
            transport=transport,
            metadata=dict(metadata or {}),
        )
        self._check_transport(action, transport)
        self._validate(action, payload)
        self._check_rules(action, payload, context)
        try:
            value = self._call_handler(action, payload, context)
            if inspect.isawaitable(value):
                if hasattr(value, "close"):
                    value.close()
                raise ActionExecutionError(
                    action.name,
                    "Async action handlers are not supported by ActionDispatcher.execute; use an async dispatcher.",
                )
        except ActionError:
            raise
        except PermissionError as exc:
            raise ActionPermissionDenied(action.name, str(exc)) from exc
        except Exception as exc:
            raise ActionExecutionError(action.name, str(exc)) from exc
        value, is_stream, stream_metadata = _normalize_action_value(value)
        return ActionResult(
            action_name=action.name,
            value=value,
            transport=transport,
            is_stream=is_stream,
            metadata={"stream": stream_metadata} if is_stream else {},
        )

    @staticmethod
    def _check_transport(action: ActionContract, transport: str | None) -> None:
        if transport is None or not action.transports:
            return
        if transport not in action.transports:
            raise ActionPermissionDenied(
                action.name,
                f"Transport '{transport}' is not allowed for action: {action.name}",
            )

    @staticmethod
    def _validate(action: ActionContract, payload: dict[str, Any]) -> None:
        try:
            validate(instance=payload, schema=action.input_schema)
        except ValidationError as exc:
            raise ActionValidationError(action.name, exc.message, data={"path": list(exc.path)}) from exc

    @staticmethod
    def _check_rules(action: ActionContract, payload: dict[str, Any], context: ActionContext) -> None:
        for rule in action.rules:
            if not callable(rule):
                continue
            try:
                allowed = rule(payload, context)
            except ActionError:
                raise
            except PermissionError as exc:
                raise ActionPermissionDenied(action.name, str(exc)) from exc
            except Exception as exc:
                raise ActionExecutionError(action.name, str(exc)) from exc
            if not allowed:
                raise ActionPermissionDenied(action.name, f"Permission denied by rule: {_rule_name(rule)}")

    @staticmethod
    def _call_handler(action: ActionContract, payload: dict[str, Any], context: ActionContext):
        if action.handler is None:
            raise ActionExecutionError(action.name, f"Action has no handler: {action.name}")
        signature = inspect.signature(action.handler)
        parameters = list(signature.parameters.values())
        if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters):
            return action.handler(payload=payload, context=context)
        if len(parameters) == 0:
            return action.handler()
        if len(parameters) == 1:
            if parameters[0].name in ("context", "action_context"):
                return action.handler(context)
            return action.handler(payload)
        return action.handler(payload, context)


def _handler_ref(handler: Callable[..., Any]) -> str:
    return f"{getattr(handler, '__module__', '')}.{getattr(handler, '__name__', '')}".strip(".")


def _rule_name(rule: Any) -> str:
    return getattr(rule, "name", None) or getattr(rule, "__name__", None) or str(rule)


def _rule_contract(rule: Any) -> Any:
    if isinstance(rule, str):
        return rule
    if isinstance(rule, dict):
        return rule
    return _rule_name(rule)


def _normalize_action_value(value: Any) -> tuple[Any, bool, dict[str, Any]]:
    if isinstance(value, StreamResult):
        return value, True, dict(value.metadata)
    if _is_stream_result(value):
        stream = StreamResult(source=value)
        return stream, True, dict(stream.metadata)
    return value, False, {}


def _is_stream_result(value: Any) -> bool:
    if isinstance(value, (str, bytes, dict, list, tuple)):
        return False
    return isinstance(value, Iterable)


def coerce_stream_event(item: StreamEvent | dict[str, Any]) -> StreamEvent:
    if isinstance(item, StreamEvent):
        return item
    if isinstance(item, dict):
        event_type = str(item.get("type", item.get("event", "progress")))
        if "data" in item:
            data = item.get("data")
        else:
            data = {key: value for key, value in item.items() if key not in {"type", "event", "id", "event_id", "metadata"}}
        event_id = item.get("event_id", item.get("id"))
        metadata = item.get("metadata") or {}
        return StreamEvent(type=event_type, data=data, event_id=event_id, metadata=dict(metadata))
    raise TypeError("Stream items must be StreamEvent or mapping")


def stream_events(result: StreamResult | Iterable[StreamEvent | dict[str, Any]]):
    stream = result if isinstance(result, StreamResult) else StreamResult(source=result)
    try:
        for item in stream:
            try:
                yield coerce_stream_event(item)
            except Exception as exc:
                yield StreamEvent(type="error", data={"code": "stream_error", "message": str(exc)})
                break
    except Exception as exc:
        yield StreamEvent(type="error", data={"code": "stream_error", "message": str(exc)})
    finally:
        stream.close_source()
