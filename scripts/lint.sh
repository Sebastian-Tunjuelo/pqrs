#!/usr/bin/env bash
# Lint local: ruff + black (Python), opcionalmente Rust y Prettier si hay herramientas en PATH.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
FAIL=0

py_paths=(shared-kernel contexts orchestration e2e scripts)

echo "==> ruff"
if "${PYTHON}" -m ruff check "${py_paths[@]}" 2>/dev/null; then
  :
else
  echo "[lint] Falló ruff o no está instalado (pip install ruff)."
  FAIL=1
fi

echo "==> black --check"
if "${PYTHON}" -m black --check "${py_paths[@]}" 2>/dev/null; then
  :
else
  echo "[lint] Falló black o no está instalado (pip install black)."
  FAIL=1
fi

echo "==> Rust (contexts/api)"
if command -v cargo >/dev/null 2>&1; then
  (cd contexts/api && cargo fmt --check && cargo clippy --quiet -- -D warnings) || FAIL=1
else
  echo "[lint] cargo no en PATH; omitiendo fmt/clippy."
fi

echo "==> Prettier (presentation)"
if command -v npx >/dev/null 2>&1 && [[ -f contexts/presentation/package.json ]]; then
  (cd contexts/presentation && npx prettier --check "app/**/*.{tsx,ts,css}" "components/**/*.{tsx,ts}" "lib/**/*.{ts,tsx}" 2>/dev/null) || {
    echo "[lint] Prettier falló o faltan dependencias (npm install en contexts/presentation)."
    FAIL=1
  }
else
  echo "[lint] npx no disponible; omitiendo Prettier."
fi

exit "${FAIL}"
