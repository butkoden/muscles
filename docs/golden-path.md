# Muscles Golden Path Structure

Official Muscles project structure:

```text
app/
  application.py
  config.py
  domain/
  schemas/
  web/
  api/
  cli/
  rules/
  templates/
  static/
tests/
```

## Directory Purposes

- `app/application.py`: main application class, context, strategy wiring.
- `app/config.py`: runtime configuration and mode-specific values.
- `app/domain/`: entities, value objects, domain services/use cases.
- `app/schemas/`: request/response and shared schema models.
- `app/web/`: page routes and web handlers.
- `app/api/`: REST controllers/actions and API metadata.
- `app/cli/`: command groups and command handlers.
- `app/rules/`: reusable rules/security metadata attached to routes/actions/commands.
- `app/templates/`: web templates.
- `app/static/`: static assets for web runtime.
- `tests/`: unit/integration/smoke tests.

## Layer Rules

- Do not place route/action handlers outside `web/`, `api/`, `cli/`.
- Describe input/output with schemas in `schemas/`.
- Keep domain invariants in value objects (`domain/`).
- Do not duplicate business logic between HTTP and CLI handlers.
- Move shared business logic to domain services/use cases in `domain/`.

## Minimal Variant

Use for CLI-only or small runtime experiments:

```text
app/
  application.py
  config.py
  domain/
  schemas/
  cli/
tests/
```

## Full Variant

Use for multi-interface applications (Web + API + CLI):

```text
app/
  application.py
  config.py
  domain/
  schemas/
  web/
  api/
  cli/
  rules/
  templates/
  static/
tests/
```

## Synchronization Contract

- `muscles-cli` project scaffolding (`muscles new`) should generate this structure.
- Golden tutorial should use this structure as source of truth.
