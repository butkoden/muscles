# Muscles Roadmap Baseline

This document fixes a single execution baseline for roadmap tasks and their acceptance checks.

## Execution Order

1. `muscles#14` Naming standardization.
2. `muscles#15` Unified install scenario.
3. `muscles#17` Positioning.
4. `muscles#25` Golden path structure.
5. `muscles-cli#3` `muscles new`.
6. `muscles#26` Runtime modes (`development|test|production`).
7. `muscles#22` Self-describing inspection contract.
8. `muscles-cli#8` `muscles capabilities --json`.
9. `muscles-cli#4` `inspect/routes/schemas/rules/cli`.
10. `muscles-cli#7` Generators.
11. `muscles-cli#6` `muscles doctor`.
12. `muscles-cli#5` `muscles test`.
13. `muscles#16` Golden tutorial.
14. `muscles#24` AI recipes.
15. `muscles#23` Pydantic/JSON Schema bridge.
16. `muscles#18` Production deploy docs (WSGI/ASGI).
17. `muscles#20` Benchmarks.
18. `muscles#19` Value objects and rules/security examples.
19. `muscles#21` CONTRIBUTING and onboarding.

## Current Status At Baseline Time

- `muscles#14` is already `CLOSED` upstream.
- Remaining tasks in this sequence are `OPEN`.
- `develop` branches are created and pushed for:
  - `muscles`
  - `muscles-cli`
  - `muscles-wsgi`
  - `muscles-asgi`
  - `muscular-example`

## Global Rules For This Program

- Canonical naming: public name is `Muscles`; technical identifiers stay lowercase (`muscles`, `muscles-*`).
- Use TDD for implementation tasks: add/adjust tests first or together with behavior.
- After each completed task:
  - verify against issue requirements;
  - run relevant test suites;
  - merge to `develop`.
- No breaking changes for existing import paths unless explicitly defined by issue scope.

## Task Requirements Snapshot

### `muscles#14` Naming

- Keep `Muscles` as public brand.
- Keep `muscles` package name.
- Remove non-canonical user-facing `Muscular` wording.
- Keep runtime behavior unchanged.

### `muscles#15` Install scenario

- Document canonical install matrix:
  - core only
  - ASGI
  - WSGI
  - CLI
  - full/dev
- Define packaging strategy clearly (matrix vs extras/metapackage).
- Add downstream follow-up checklist.

### `muscles#17` Positioning

- Add explicit positioning section in README/docs.
- Include `when to use / when not to use`.
- Add honest FastAPI comparison note.

### `muscles#25` Golden path structure

- Publish official project structure and layer boundaries.
- Sync structure with tutorial and scaffolding.

### `muscles-cli#3` `muscles new`

- Generate runnable scaffold per runtime (`asgi|wsgi|cli`, optional full).
- Add safety for non-empty directories (`--force` required to overwrite).
- Generate tests and runnable instructions.

### `muscles#26` Runtime modes

- Introduce canonical modes: `development`, `test`, `production`.
- Resolve mode from env/config/CLI override.
- Restrict sensitive diagnostics and metadata in production.

### `muscles#22` Self-describing contract

- Add stable, versioned inspection contract in core.
- Include routes/schemas/rules/handlers/strategies/config metadata (no secrets).

### `muscles-cli#8` Capabilities discovery

- Add `muscles capabilities [--json]`.
- Include capability metadata: mutating/dev-only/production-safe flags.
- Include contract version and recommended AI workflow.

### `muscles-cli#4` Introspection commands

- Add inspect/routes/schemas/rules/cli commands.
- Use core inspection API, not ad-hoc file parsing.

### `muscles-cli#7` Generators

- Add page/api-resource/cli-command/value-object/resource generators.
- Generate tests by default (or equivalent explicit flag).

### `muscles-cli#6` Doctor

- Add project diagnostics (`muscles doctor`, `--json`) with severity/codes/fixes.

### `muscles-cli#5` Test

- Add canonical test runner command for Muscles projects.

### `muscles#16` Golden tutorial

- End-to-end tutorial for Web + API + CLI + tests + Docker.
- Runnable and validated by smoke tests.

### `muscles#24` AI recipes

- Add official AI instructions docs and link them from README.

### `muscles#23` Pydantic bridge

- Add optional compatibility bridge for Pydantic and JSON Schema export.

### `muscles#18` Production deploy docs

- Add umbrella deploy docs plus WSGI/ASGI runtime specifics.

### `muscles#20` Benchmarks

- Add reproducible benchmark suite and publish first results with environment notes.

### `muscles#19` Value objects/rules examples

- Add practical examples and tests for documented behavior.

### `muscles#21` CONTRIBUTING

- Add contributor onboarding, test commands, PR checklist and first-issue guidance.

## Verification Model Per Task

1. Requirement checklist from corresponding issue body.
2. Focused tests for changed behavior.
3. Full project test suite where change touches shared/core behavior.
4. Documentation link check for changed docs sections.
