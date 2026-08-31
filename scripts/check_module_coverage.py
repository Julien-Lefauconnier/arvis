# scripts/check_module_coverage.py
"""Gate check: per-package coverage floors for the decisive packages.

The aggregate 90% floor let a 59%-covered gate-policy module hide
inside a 91% total (audit G4, 2026-08). The packages whose lines decide
verdicts and access now carry their own floors, read from the coverage
JSON the gate produces.

Floors ratchet: they are set just under the measured coverage at
introduction and may be raised, never lowered without a dated
justification here.

Usage: python scripts/check_module_coverage.py [coverage.json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# package prefix -> floor (percent). Set 2026-08-31 (campaign MATH-A,
# LOT M3) just under the measured values of the day.
FLOORS: dict[str, float] = {
    "arvis/math/gate/": 97.0,
    "arvis/math/core/": 95.0,
    "arvis/math/lyapunov/": 93.0,
    "arvis/kernel_core/access/": 93.0,
    "arvis/kernel/gate/": 95.0,
}


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "coverage.json"
    if not path.exists():
        print(f"check_module_coverage: {path} not found (run the gate pytest first)")
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    files: dict[str, dict] = data.get("files", {})

    failures: list[str] = []
    for prefix, floor in FLOORS.items():
        covered = 0
        statements = 0
        for filename, entry in files.items():
            normalized = filename.replace("\\", "/")
            if normalized.startswith(prefix):
                summary = entry.get("summary", {})
                covered += int(summary.get("covered_lines", 0))
                statements += int(summary.get("num_statements", 0))
        if statements == 0:
            failures.append(f"{prefix}: no measured statements (package moved?)")
            continue
        percent = 100.0 * covered / statements
        status = "ok" if percent >= floor else "FAIL"
        print(
            f"check_module_coverage: {prefix:<28} {percent:6.2f}% "
            f"(floor {floor:.1f}%) {status}"
        )
        if percent < floor:
            failures.append(f"{prefix}: {percent:.2f}% < floor {floor:.1f}%")
    if failures:
        print("\nper-package coverage floors violated:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
