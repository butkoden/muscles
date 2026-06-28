#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

printf '%s\n' "[muscles ai-bootstrap] repository: $(git rev-parse --abbrev-ref HEAD)"

for cmd in git python3 make; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[muscles ai-bootstrap] ERROR: required command '$cmd' not found"
    exit 1
  fi
  echo "[muscles ai-bootstrap] OK: $cmd"
done

if [[ -f AGENTS.md ]]; then
  echo "[muscles ai-bootstrap] OK: AGENTS.md"
elif [[ -f docs/ai/AGENTS.md ]]; then
  echo "[muscles ai-bootstrap] OK: docs/ai/AGENTS.md"
else
  echo "[muscles ai-bootstrap] ERROR: AGENTS file not found"
  exit 1
fi

[[ -f docs/ai/environment-bootstrap.md ]] || { echo '[muscles ai-bootstrap] ERROR: docs/ai/environment-bootstrap.md missing'; exit 1; }

if [[ -d src/muscles ]]; then
  echo "[muscles ai-bootstrap] src packages: $(find src/muscles -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ')"
fi

echo '[muscles ai-bootstrap] repository bootstrap complete'
