# План выпуска Muscles RC

Линия RC основана на core `1.0.0rc1`; зависимости используют диапазон
`>=1.0.0rc1,<2.0.0`. Runtime- и extension-пакеты не должны зависеть от Git-
ветки или локального checkout во время установки.

## Порядок публикации

1. `muscles`
2. runtime: `muscles-asgi`, `muscles-wsgi`, `muscles-cli`
3. projections: `muscles-jsonrpc`, `muscles-sse`, `muscles-mcp`
4. extensions: `muscles-sql`, `muscles-otel`, `muscles-ai`, `muscles-documents`, `muscles-data`
5. production data adapters
6. gate `muscles-benchmarks` и итоговый compatibility report

## Gate

Перед RC нужно выполнить `make ai-bootstrap`, `make ecosystem-test` и
`make clean-install-smoke`: команда собирает wheel каждого пакета, устанавливает
все локальные артефакты в чистое окружение без `PYTHONPATH` и запускает общий
benchmark smoke. Отдельно release workflow каждого пакета собирает wheel и
sdist; в отчёте benchmark список `thresholds.failed` должен быть пустым.

## Откат

Публиковать пакеты в указанном порядке. Если поздний пакет не проходит smoke-
проверку артефакта или совместимости, остановить публикацию, оставить
последнюю зелёную версию поддерживаемой и не публиковать зависимые пакеты до
исправления диапазона зависимостей или реализации.
