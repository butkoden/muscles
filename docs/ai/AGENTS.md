## Muscles AI Instructions

## Required Workflow

- Старт с чтения `AGENTS.md`, `docs/ai/AGENTS.md` и `docs/ai/environment-bootstrap.md`.
- Запуск `make ai-bootstrap`.
- Затем, по задаче: `muscles capabilities --json`, `muscles inspect --json`, `muscles generate ...`, `muscles doctor --json`, `muscles test`.

## Rules

- Следовать golden path структуре.
- Не создавать handlers вне `app/web`, `app/api`, `app/cli`.
- Вход/выход только через схемы.
- Инварианты держать во value objects.
- Не дублировать бизнес-логику между HTTP и CLI обработчиками.
- Не переименовывать технические идентификаторы без явной миграции.
