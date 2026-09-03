#!/usr/bin/env bash
# scripts/build_docs.sh
#
# Strict documentation-site build; a local writer and the CI docs job
# run the same thing. Requires the hash-locked docs environment:
#   pip install -r requirements/docs.lock --require-hashes
#   pip install -e . --no-deps
set -euo pipefail
PY="${PYTHON:-python3}"
"$PY" -m mkdocs build --strict --site-dir "${SITE_DIR:-site}"
echo "site built: ${SITE_DIR:-site}/"
