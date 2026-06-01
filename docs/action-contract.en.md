# Action Contract And Dispatcher

Muscles actions are first-class application contracts. An action is declared
once in the application-scoped registry and can be called by different protocol
projections: HTTP, CLI, MCP, JSON-RPC, SSE, and future transports.

## Declare An Action

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

## Inspect The Contract

`inspect_application(app)` is the discovery source of truth. Protocol packages
must build tools, methods, resources, or stream metadata from this contract
instead of keeping their own registries.

```python
contract = inspect_application(app)
actions = contract["actions"]
```

## Execute An Action

```python
result = ActionDispatcher(app).execute(
    "bookings.create",
    {"title": "Discovery call"},
    transport="mcp",
)
```

Validation, rules/security checks, handler execution, and result normalization
happen in core. A protocol layer should only serialize request and response
shapes.

## Errors

Core action errors are stable and intended for protocol mappings:

- `ActionNotFound`;
- `ActionValidationError`;
- `ActionPermissionDenied`;
- `ActionExecutionError`.

## State Isolation

Actions are stored in the application-scoped `ApplicationRegistry`. New protocol
projections should not use mutable module-level state as their source of truth.
