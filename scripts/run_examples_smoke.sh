#!/usr/bin/env bash
#
# Smoke test: run all ARVIS examples and fail if any aborts.
#
set -u

PY="${PYTHON:-python3}"
export PYTHONPATH=".:${PYTHONPATH:-}"

EXAMPLES=(
  examples/00_quickstart_engine.py
  examples/01_gate_refusal.py
  examples/02_deterministic_replay.py
  examples/03_ir_export.py
  examples/04_human_confirmation.py
  examples/05_tool_authorization.py
  examples/06_finance_risk_screening.py
  examples/08_timeline_audit.py
  examples/09_multi_engine_hosting.py
  examples/10_runtime_inspection.py
)

failures=()
for ex in "${EXAMPLES[@]}"; do
  if "$PY" "$ex" > /dev/null 2>&1; then
    echo "PASS  $ex"
  else
    echo "FAIL  $ex"
    failures+=("$ex")
  fi
done

if [ "${#failures[@]}" -ne 0 ]; then
  echo ""
  echo "Smoke failed: ${#failures[@]} example(s) aborted:"
  printf '  %s\n' "${failures[@]}"
  exit 1
fi

echo ""
echo "All ${#EXAMPLES[@]} examples passed."
