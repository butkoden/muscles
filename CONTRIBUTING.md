# Contributing To Muscles

## Local Setup

```bash
git clone https://github.com/butkoden/muscles.git
cd muscles
PYTHONPATH=src python -m pytest -q
```

## Repository Roles

- `muscles`: core primitives and contracts.
- `muscles-asgi`: ASGI runtime adapter.
- `muscles-wsgi`: WSGI runtime adapter.
- `muscles-cli`: CLI runtime and developer tooling.

## Pull Request Checklist

- tests are added/updated;
- `PYTHONPATH=src python -m pytest -q` passes;
- docs updated for user-facing behavior;
- no accidental breaking rename of package identifiers.

## Good First Contribution Areas

- docs wording/links;
- example improvements;
- value object examples;
- benchmark smoke improvements;
- naming consistency checks.
