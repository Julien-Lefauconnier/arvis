#!/usr/bin/env bash
# Canonical local/CI quality gate for ARVIS.
#
# One definition per check, here. CI parallelizes into separate jobs,
# so the script exposes the granularity those jobs need rather than a
# single all-or-nothing entry point: a workflow selects a mode, it
# never spells a check's command out itself. That parity is enforced
# by tests/tooling/test_ci_gate_parity.py, because the previous
# hand-copied arrangement let the newest check (the broad-except
# ratchet) exist in the gate and in no workflow.
#
# Modes:
#   static    formatting, lint, types, docs and header integrity,
#             broad-except discipline
#   security  bandit
#   audit     pip-audit against the locked environment
#   tests     pytest with coverage plus the per-package floors
#   examples  the stable examples smoke
#   all       everything above, in that order (the local default)
set -euo pipefail

PY="${PYTHON:-python3}"
MODE="${1:-all}"

run_static_gate() {
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

  echo "==> Broad except discipline"
  "$PY" scripts/check_broad_excepts.py
}

run_security_gate() {
  echo "==> Bandit (medium/high)"
  "$PY" -m bandit -r arvis -ll -q
}

run_audit_gate() {
  # Known vulnerabilities in the resolved dependency set, blocking
  # (audit a13, P1-03): the environment is locked, so a failure here
  # is actionable and never noise from unrelated work.
  #
  # PIP_AUDIT lets a caller point at an isolated installation, so
  # pip-audit's own transitives never enter the frozen gate
  # environment they are meant to audit (campaign CI).
  #
  # Exceptions are explicit --ignore-vuln flags listed HERE, once,
  # with a dated justification, per the policy in SECURITY.md. They
  # used to be copy-pasted into two workflows with the justification
  # in only one, so removing one left the other silently suppressing.
  #
  # No active suppression (campaign HARDEN, 2026-09-02): the pytest 9
  # toolchain bump closed PYSEC-2026-1845, the last ignored advisory.
  echo "==> Dependency audit"
  "${PIP_AUDIT:-pip-audit}" --strict \
    -r requirements/gate.lock
}

run_tests_gate() {
  echo "==> Pytest with coverage"
  "$PY" -m pytest \
    --cov=arvis \
    --cov-report=term-missing \
    --cov-report=json:coverage.json \
    --cov-fail-under=90 \
    -q

  echo "==> Per-package coverage floors"
  "$PY" scripts/check_module_coverage.py coverage.json
}

run_examples_gate() {
  echo "==> Examples smoke"
  PYTHON="$PY" bash scripts/run_examples_smoke.sh
}

run_full_gate() {
  run_static_gate
  run_security_gate
  run_tests_gate
  run_examples_gate
}

case "$MODE" in
  all)
    run_full_gate
    ;;
  static)
    run_static_gate
    ;;
  security)
    run_security_gate
    ;;
  audit)
    run_audit_gate
    ;;
  tests)
    run_tests_gate
    ;;
  examples)
    run_examples_gate
    ;;
  *)
    echo "usage: $0 [all|static|security|audit|tests|examples]" >&2
    exit 2
    ;;
esac
