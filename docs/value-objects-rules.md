# Value Objects And Rules Examples

## Value Objects

Examples available in core:

- `EmailValue`
- `MoneyValue`
- `SlugValue`
- `DateRangeValue`
- `PhoneValue`

Use `ValueObjectField` in models to keep domain invariants near schema declarations.

## Rules/Security

Attach rules close to route/action/command metadata:

- route-level permission for pages;
- API action security metadata for OpenAPI projection;
- CLI command rule checks before handler execution.

## Practical Guidance

- Keep validation and serialization rules in value objects.
- Reuse the same value object across API/Web/CLI.
- Keep authorization metadata declarative and transport-agnostic.
