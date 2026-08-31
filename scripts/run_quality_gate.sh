#!/usr/bin/env bash
# Canonical local/CI quality gate for ARVIS.
set -euo pipefail

PY="${PYTHON:-python3}"
MODE="${1:-all}"

run_security_gate() {
  echo "==> Bandit (medium/high)"
  "$PY" -m bandit -r arvis -ll -q
}

run_full_gate() {
  echo "==> Ruff format"
  "$PY" -m ruff format --check .

  echo "==> Ruff lint"
  "$PY" -m ruff check .

  echo "==> Mypy strict"
  "$PY" -m mypy arvis --strict

  echo "==> Markdown path references"
  "$PY" scripts/check_md_refs.py

  echo "==> Path headers"
  "$PY" scripts/check_path_headers.py

  run_security_gate

  echo "==> Pytest with coverage"
  "$PY" -m pytest \
    --cov=arvis \
    --cov-report=term-missing \
    --cov-report=json:coverage.json \
    --cov-fail-under=90 \
    -q

  echo "==> Per-package coverage floors"
  "$PY" scripts/check_module_coverage.py coverage.json

  echo "==> Examples smoke"
  PYTHON="$PY" bash scripts/run_examples_smoke.sh
}

case "$MODE" in
  all)
    run_full_gate
    ;;
  security)
    run_security_gate
    ;;
  *)
    echo "usage: $0 [all|security]" >&2
    exit 2
    ;;
esac
