# Action Contract и Dispatcher

Actions в Muscles — это first-class contract приложения. Action объявляется один
раз в application-scoped registry и может вызываться разными protocol
projections: HTTP, CLI, MCP, JSON-RPC, SSE и будущими transports.

## Объявление action

```python
app = BookingApp()


@app.action(
    name="bookings.create",
    description="Create a booking request",
    input_schema={
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
    },
    transports=["http", "cli", "mcp"],
)
def create_booking(payload, context):
    return {"title": payload["title"], "transport": context.transport}
```

## Inspect contract

`inspect_application(app)` — источник истины для discovery. Protocol packages
должны строить tools, methods, resources или stream metadata из этого contract,
а не держать собственные реестры.

```python
contract = inspect_application(app)
actions = contract["actions"]
```

## Выполнение action

```python
result = ActionDispatcher(app).execute(
    "bookings.create",
    {"title": "Discovery call"},
    transport="mcp",
)
```

Валидация, rules/security checks, вызов handler и нормализация результата
происходят в core. Protocol layer должен только сериализовать request и
response shapes.

## Ошибки

Core action errors стабильны и рассчитаны на protocol mappings:

- `ActionNotFound`;
- `ActionValidationError`;
- `ActionPermissionDenied`;
- `ActionExecutionError`.

## Изоляция состояния

Actions хранятся в application-scoped `ApplicationRegistry`. Новые protocol
projections не должны использовать mutable module-level state как источник
истины.
