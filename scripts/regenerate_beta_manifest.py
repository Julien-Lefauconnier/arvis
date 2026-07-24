#!/usr/bin/env python3
# scripts/regenerate_beta_manifest.py

"""Regenerate the beta contract manifest golden file.

Changing the golden is changing the supported beta surface: run this
deliberately, review the diff, and record the change in the changelog
(and bump HOST_API_VERSION if a host_api module moved).
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.contracts.beta_manifest import generate_manifest  # noqa: E402

GOLDEN = ROOT / "tests" / "contracts" / "beta_contract_manifest.json"


def main() -> None:
    manifest = generate_manifest()
    GOLDEN.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"written: {GOLDEN.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
