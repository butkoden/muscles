# Muscles Installation

This page defines canonical installation paths for the Muscles ecosystem.

## Current Distribution Status

- Public framework name: `Muscles`.
- Technical package names follow the `muscles-*` ecosystem convention.
- Current canonical install method: PyPI for release artifacts; GitHub source
  installs remain available for development checkouts.
- The current release-candidate core is `muscles==1.0.0rc3`.

## Install Matrix

### Core Only

```bash
pip install "muscles>=1.0.0rc3,<2.0.0"
```

Use this when you need shared primitives only: application model, schemas, routing tree, lifecycle and rules metadata.

### ASGI Web/API Runtime

```bash
pip install muscles-asgi
```

Use this when your app runtime is ASGI.

### WSGI Web/API Runtime

```bash
pip install muscles-wsgi
```

Use this when your app runtime is WSGI.

### CLI Tooling

```bash
pip install muscles-cli
```

Use this for command routing and console strategy support.

### Protocol Projections

```bash
pip install git+https://github.com/butkoden/muscles-jsonrpc.git
pip install git+https://github.com/butkoden/muscles-sse.git
pip install muscles-mcp
```

Use these when an application action model must be exposed through JSON-RPC,
Server-Sent Events or Model Context Protocol.

### Framework Extensions

```bash
pip install muscles-sql
pip install git+https://github.com/butkoden/muscles-otel.git
pip install git+https://github.com/butkoden/muscles-documents.git
pip install muscles-ai
```

Use these for SQL persistence, observability, document ingestion and read-only
AI/RAG flows that should remain transport-agnostic.

### Full/Development Setup (All Repositories)

```bash
git clone https://github.com/butkoden/muscles.git
git clone https://github.com/butkoden/muscles-asgi.git
git clone https://github.com/butkoden/muscles-wsgi.git
git clone https://github.com/butkoden/muscles-cli.git
git clone https://github.com/butkoden/muscles-jsonrpc.git
git clone https://github.com/butkoden/muscles-sse.git
git clone https://github.com/butkoden/muscles-mcp.git
git clone https://github.com/butkoden/muscles-sql.git
git clone https://github.com/butkoden/muscles-otel.git
git clone https://github.com/butkoden/muscles-documents.git
git clone https://github.com/butkoden/muscles-ai.git
git clone https://github.com/butkoden/muscles-benchmarks.git
```

Run tests from each repository with sibling `src` paths on `PYTHONPATH`:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-asgi/src:../muscles-cli/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-mcp/src:../muscles-sql/src:../muscles-otel/src:../muscles-documents/src:../muscles-ai/src python -m pytest -q
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
- Protocol packages (`muscles-jsonrpc`, `muscles-sse`, `muscles-mcp`):
  - README points to core and explains which projection it owns.
  - Public behavior is discovered from core actions/inspect contracts.
- Extension packages (`muscles-sql`, `muscles-otel`, `muscles-documents`, `muscles-ai`):
  - README points to core and explains which framework capability it owns.
  - Capabilities stay transport-agnostic and expose behavior through actions or explicit runtime hooks.
- `muscles-benchmarks`:
  - README documents which package owns each benchmark surface.
  - Regression reports include core, runtime, protocol and extension coverage.

## Notes For `muscles new`

Generated projects should:

- declare dependencies according to selected runtime;
- avoid ambiguous package names;
- keep explicit link to this installation page in generated README.
