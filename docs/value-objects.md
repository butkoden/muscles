# Value Objects

This guide explains how to use Value Objects in Muscles without breaking
existing `Field`/`Column` code.

## Why

Value Objects let you keep domain rules near data:

- immutable value semantics;
- strict validation at construction;
- equality by value;
- reusable behavior across API/CLI/DB flows.

## Core API

Available base classes and adapters:

- `ValueObject`
- `ValueObjectField`

Built-in examples:

- `EmailValue`
- `PhoneValue`
- `DateRangeValue`
- `DateTimeRangeValue`
- `UtcDateTimeValue`
- `SlugValue`
- `UrlValue`
- `CountryCodeValue`
- `PercentageValue`
- `MoneyValue`
- `NonEmptyStringValue`

## Minimal example

```python
from muscles import Model, Column, ValueObject, ValueObjectField


class EmailAddress(ValueObject):
    def normalize(self, value):
        return str(value).strip().lower()

    def validate(self, value):
        if "@" not in value:
            raise ValueError("email must contain @")
        return True


class Contact(Model):
    email = Column(ValueObjectField(value_object_class=EmailAddress))
```

Result:

- `Contact(email="USER@EXAMPLE.COM ").email` becomes `EmailAddress("user@example.com")`
- `Contact(...).as_dict()["email"]` returns primitive `"user@example.com"`

## Runtime validation pattern

To enforce ValueObject validation in handlers, instantiate model from input
before persistence:

```python
payload = Booking(**request.json).as_dict()
save_booking(payload)
```

If a ValueObject fails, return `400` with validation details.

## Migration strategy

1. Keep existing primitive fields working.
2. Replace one field at a time with `ValueObjectField`.
3. Add/adjust runtime validation in endpoint/command layer.
4. Add regression tests for both valid and invalid inputs.

This keeps OpenAPI/routing contracts stable while introducing stricter domain
rules.
