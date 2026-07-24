#!/usr/bin/env bash
# scripts/run_blackbox_against_wheel.sh
#
# Build the wheel, install it in a pristine virtual environment, and run
# the black-box compliance suite against the INSTALLED package (audit
# a13, P1-01). The suite is copied out of the repository so the source
# tree is not importable: what passes here is the wheel, nothing else.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "==> building the wheel"
python -m pip wheel --no-deps -w "$WORKDIR/dist" "$ROOT" > /dev/null
WHEEL="$(ls "$WORKDIR"/dist/arvis-*.whl)"

echo "==> pristine environment"
python -m venv "$WORKDIR/venv"
"$WORKDIR/venv/bin/python" -m pip install --quiet --upgrade pip
"$WORKDIR/venv/bin/python" -m pip install --quiet "$WHEEL" pytest

echo "==> running the black-box suite against $WHEEL"
mkdir -p "$WORKDIR/suite"
cp "$ROOT"/compliance/blackbox/test_blackbox_contract.py "$WORKDIR/suite/"
cd "$WORKDIR/suite"
BLACKBOX_REQUIRE_WHEEL=1 "$WORKDIR/venv/bin/python" -m pytest -q test_blackbox_contract.py

echo "==> black-box compliance: PASS (installed wheel)"
