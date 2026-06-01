# Muscles Installation

This page defines canonical installation paths for the Muscles ecosystem.

## Current Distribution Status

- Public framework name: `Muscles`.
- Technical package names: `muscles`, `muscles-asgi`, `muscles-wsgi`, `muscles-cli`.
- Current canonical install method: GitHub source installs.
- Target state: publish stable package releases to PyPI.

## Install Matrix

### Core Only

```bash
pip install git+https://github.com/butkoden/muscles.git
```

Use this when you need shared primitives only: application model, schemas, routing tree, lifecycle and rules metadata.

### ASGI Web/API Runtime

```bash
pip install git+https://github.com/butkoden/muscles-asgi.git
```

Use this when your app runtime is ASGI.

### WSGI Web/API Runtime

```bash
pip install git+https://github.com/butkoden/muscles-wsgi.git
```

Use this when your app runtime is WSGI.

### CLI Tooling

```bash
pip install git+https://github.com/butkoden/muscles-cli.git
```

Use this for command routing and console strategy support.

### Full/Development Setup (All Repositories)

```bash
git clone https://github.com/butkoden/muscles.git
git clone https://github.com/butkoden/muscles-asgi.git
git clone https://github.com/butkoden/muscles-wsgi.git
git clone https://github.com/butkoden/muscles-cli.git
```

Run tests from each repository with sibling `src` paths on `PYTHONPATH`:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-asgi/src:../muscles-cli/src python -m pytest -q
```

## Packaging Decision For Now

Current decision is **option C**:

- keep separate ecosystem packages;
- provide a clear install matrix;
- avoid introducing a metapackage until release cadence and dependency constraints are stabilized.

Planned follow-up:

- evaluate extras (`muscles[asgi,wsgi,cli]`) after base package publishing flow is stable;
- evaluate metapackage only if extras cannot express required dependency split.

## Follow-up Checklist For Ecosystem Repositories

- `muscles-asgi`:
  - README points to this install matrix.
  - Package description is non-empty and aligned with Muscles naming.
- `muscles-wsgi`:
  - README points to this install matrix.
  - Package description is non-empty and aligned with Muscles naming.
- `muscles-cli`:
  - README points to this install matrix.
  - Package description is non-empty and aligned with Muscles naming.
  - `muscles new` templates should consume this matrix as source of truth.

## Notes For `muscles new`

Generated projects should:

- declare dependencies according to selected runtime;
- avoid ambiguous package names;
- keep explicit link to this installation page in generated README.
