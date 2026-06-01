# Golden Tutorial

This tutorial path demonstrates one Muscles application model reused in Web, API and CLI.

## Scope

- Web page route
- REST API route
- CLI command
- Shared schema and value objects
- Tests
- Docker smoke

## Reference Implementation

Use public example repository:

- `muscular-example` (synchronized with Muscles ecosystem changes)

Local smoke command:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-asgi/src:../muscles-cli/src pytest -q
```

## Flow

1. Create project (`muscles new`).
2. Define schema and value object.
3. Add API/Web/CLI handlers.
4. Run `muscles inspect --json`.
5. Run `muscles doctor`.
6. Run `muscles test`.

## Docker

Use generated Dockerfile/docker-compose from `muscles new --runtime asgi|wsgi`.
