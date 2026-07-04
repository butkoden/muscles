# Muscles Repository Map

This document is the quick ownership map for the Muscles framework ecosystem.
Use it when deciding where documentation, behavior, benchmarks or examples
should live.

## Core

| Repository | Responsibility |
| --- | --- |
| [`muscles`](https://github.com/butkoden/muscles) | Core application model, actions, schemas, routing, context/strategy contracts, dependency primitives and canonical framework documentation. |

## Runtimes

| Repository | Responsibility |
| --- | --- |
| [`muscles-asgi`](https://github.com/butkoden/muscles-asgi) | ASGI projection for HTTP/API applications, OpenAPI/Swagger, typed handlers and ASGI test helpers. |
| [`muscles-wsgi`](https://github.com/butkoden/muscles-wsgi) | WSGI projection for HTTP/API applications, pages/templates/static files, OpenAPI/Swagger and WSGI test helpers. |
| [`muscles-cli`](https://github.com/butkoden/muscles-cli) | CLI projection, project scaffolding, action inspection and command execution. |

## Protocol Projections

| Repository | Responsibility |
| --- | --- |
| [`muscles-jsonrpc`](https://github.com/butkoden/muscles-jsonrpc) | JSON-RPC 2.0 methods generated from Muscles action contracts. |
| [`muscles-sse`](https://github.com/butkoden/muscles-sse) | Server-Sent Events delivery for `StreamResult` and typed `StreamEvent` action output. |
| [`muscles-mcp`](https://github.com/butkoden/muscles-mcp) | MCP tools/resources generated from `inspect_application(app)` and executed through `ActionDispatcher`. |

## Framework Extensions

| Repository | Responsibility |
| --- | --- |
| [`muscles-sql`](https://github.com/butkoden/muscles-sql) | SQL models, repositories, transactions, migrations helpers and named SQL connections. |
| [`muscles-otel`](https://github.com/butkoden/muscles-otel) | Optional OpenTelemetry instrumentation for framework lifecycle, runtime dispatch and action execution. |
| [`muscles-documents`](https://github.com/butkoden/muscles-documents) | Document source loading, parsing, chunking, metadata and sync actions. |
| [`muscles-ai`](https://github.com/butkoden/muscles-ai) | Read-only AI/RAG actions, retrieval and diagnostics that can compose with documents/data integrations. |

## Support And Examples

| Repository | Responsibility |
| --- | --- |
| [`muscles-benchmarks`](https://github.com/butkoden/muscles-benchmarks) | Golden-path benchmarks, architecture proof-suite and regression checks across core, runtimes, protocols and extensions. |
| [`muscular-example`](https://github.com/butkoden/muscular-example) | Layered learning example that demonstrates application structure and runtime usage. |
| [`muscles-landing`](https://github.com/butkoden/muscles-landing) | Product/application repository built on top of the framework. |
| [`muscular-asgi`](https://github.com/butkoden/muscular-asgi) | Deprecated ASGI compatibility package. New work should target `muscles-asgi`. |

## Ownership Rules

- Core owns contracts and protocol-neutral behavior.
- Runtime repositories own concrete protocol execution details.
- Protocol projection repositories translate core actions into external protocol envelopes.
- Extension repositories own reusable framework capabilities and expose them through actions or explicit hooks.
- Benchmark changes belong in `muscles-benchmarks`, with ownership notes for the package that should fix regressions.
- Product/application behavior belongs in application repositories such as `muscles-landing`, not in framework core.
