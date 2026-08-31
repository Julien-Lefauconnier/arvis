# scripts/add_spdx_headers.py
"""One-shot tool: add an SPDX license identifier to every source file.

The repository declares ``Apache-2.0`` in its packaging metadata but no
source file carries a license marker. This tool inserts::

    # SPDX-License-Identifier: Apache-2.0

immediately after the ``# arvis/...`` path header when one is present
(first line), or as the first line otherwise, for every tracked ``.py``
file under ``arvis/``. Files that already carry an SPDX identifier are
left untouched, so the tool is idempotent.

Run it deliberately, as its own commit (it touches every module):

    python scripts/add_spdx_headers.py          # dry run, lists files
    python scripts/add_spdx_headers.py --write  # applies the change
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPDX_LINE = "# SPDX-License-Identifier: Apache-2.0"


def _tracked_py_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "arvis/**/*.py", "arvis/*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [ROOT / line for line in out.stdout.splitlines() if line]


def main() -> int:
    write = "--write" in sys.argv
    touched = 0
    for py_file in _tracked_py_files():
        text = py_file.read_text(encoding="utf-8")
        if "SPDX-License-Identifier" in text:
            continue
        lines = text.splitlines(keepends=True)
        insert_at = 0
        if lines and lines[0].startswith("#") and lines[0].rstrip().endswith(".py"):
            insert_at = 1
        lines.insert(insert_at, SPDX_LINE + "\n")
        touched += 1
        if write:
            py_file.write_text("".join(lines), encoding="utf-8")
        else:
            print(py_file.relative_to(ROOT))
    verb = "updated" if write else "would update"
    print(f"add_spdx_headers: {verb} {touched} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
