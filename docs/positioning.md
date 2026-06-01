# Muscles Positioning

Muscles exists for teams that want one application model reused across Web, API and CLI interfaces.

## Core Statement

Muscles is not "another API microframework with different decorators".  
Muscles is a shared application model where:

- routing tree is reusable across runtimes;
- schemas are reusable across transport boundaries;
- lifecycle hooks are reusable across runtime strategies;
- rules/security metadata is attached close to handlers and remains reusable.

## What Muscles Optimizes For

- consistency between interfaces (HTTP pages, REST API, CLI commands);
- predictable structure for people and AI assistants;
- explicit metadata for inspection and automation workflows.

## What Muscles Does Not Optimize For

- minimal-code fastest "hello endpoint" experience;
- bundled enterprise stack (ORM/admin/etc.) in core;
- unverified performance claims.

## When To Use

- One domain model is consumed by both HTTP and CLI.
- Teams need deterministic architecture for AI-assisted development.
- You want route/schema/rules declarations to remain close and unified.

## When Not To Use

- Single-interface service with very small scope and no shared model pressure.
- Project constraints require a framework with larger built-in ecosystem from day one.

## Relation To FastAPI

FastAPI is a strong API-first framework and is often a better fit for pure API speed-to-market.
Muscles targets unified multi-interface application modeling rather than fastest API bootstrap.

The two approaches can coexist. Selection should be driven by architecture fit, not brand comparison.
