# Production Deploy (Umbrella)

Muscles supports both WSGI and ASGI runtime adapters.

## Recommended MVP Runtime Choices

- ASGI: `uvicorn` for async-oriented workloads.
- WSGI: `gunicorn` for classic sync workloads.

## Common Production Topics

- Environment config and runtime mode (`MUSCLES_ENV=production`)
- Secret management (env/secret store)
- Structured logging
- Health check endpoint pattern
- Reverse proxy (nginx)
- Docker image build and run

## ASGI Commands

```bash
uvicorn app.application:app --host 0.0.0.0 --port 8080
```

See ASGI runtime docs:
[muscles-asgi production notes](https://github.com/butkoden/muscles-asgi/blob/master/docs/production.md)

## WSGI Commands

```bash
gunicorn app.application:app --bind 0.0.0.0:8080
```

See WSGI runtime docs:
[muscles-wsgi production notes](https://github.com/butkoden/muscles-wsgi/blob/master/docs/production.md)
