# Muscles AI Instructions

## Required Workflow

1. `muscles capabilities --json`
2. `muscles inspect --json`
3. `muscles generate ...`
4. `muscles doctor --json`
5. `muscles test`

## Rules

- Follow golden path structure.
- Do not create handlers outside `app/web`, `app/api`, `app/cli`.
- Keep input/output in schemas.
- Keep invariants in value objects.
- Do not duplicate business logic between HTTP and CLI handlers.
- Do not rename technical identifiers without explicit migration.
