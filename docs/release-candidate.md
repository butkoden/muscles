# Muscles RC release plan

The RC line is based on core `1.0.0rc1` and uses versioned dependencies in the
range `>=1.0.0rc1,<2.0.0`. Runtime and extension packages must not depend on a
Git branch or a local checkout at install time.

## Publication order

1. `muscles`
2. runtimes: `muscles-asgi`, `muscles-wsgi`, `muscles-cli`
3. projections: `muscles-jsonrpc`, `muscles-sse`, `muscles-mcp`
4. extensions: `muscles-sql`, `muscles-otel`, `muscles-ai`, `muscles-documents`, `muscles-data`
5. production data adapters
6. `muscles-benchmarks` gate and final compatibility report

## Gate

Before tagging an RC, run `make ai-bootstrap`, `make ecosystem-test`, and
`make clean-install-smoke`. The latter builds every package wheel, installs the
local artifacts into a clean environment without `PYTHONPATH`, and runs the
cross-package benchmark smoke. Each package release workflow separately builds
wheel and sdist; the benchmark report must have an empty `thresholds.failed`
list.

## Rollback

Publish packages in the order above. If a later package fails its artifact or
compatibility smoke test, stop publication, keep the last green version as the
supported line, and publish no dependent package until the dependency range or
implementation is corrected.
