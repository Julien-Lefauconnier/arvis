# scripts/check_path_headers.py
"""Gate check: a ``# arvis/...`` first-line header must name its own file.

Most modules open with a comment carrying their repository path. A header
that names another path, a leftover from a move or a typo, is worse than
no header: it actively misleads the reader. This check enforces the
convention it verifies: a first-line comment that *looks like* a path
header must equal the file's actual repository path.

Files without a path-shaped first line are ignored (the convention is not
mandatory); files with a wrong one fail.

Exit code 0 when every header matches; 1 otherwise, listing offenders as
``actual_path: header says <claimed>``.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HEADER = re.compile(r"^#\s*([\w./-]+\.py)\s*$")


def _tracked_py_files() -> list[Path]:
    out = subprocess.run(
        [
            "git",
            "ls-files",
            "arvis/**/*.py",
            "tests/**/*.py",
            "compliance/**/*.py",
            "scripts/*.py",
            "examples/*.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [ROOT / line for line in out.stdout.splitlines() if line]


def main() -> int:
    errors: list[str] = []
    for py_file in _tracked_py_files():
        rel = py_file.relative_to(ROOT).as_posix()
        try:
            first = py_file.read_text(encoding="utf-8").splitlines()[0]
        except (IndexError, UnicodeDecodeError):
            continue
        match = HEADER.match(first)
        if match is None:
            continue
        claimed = match.group(1)
        if claimed != rel:
            errors.append(f"{rel}: header says {claimed}")
    if errors:
        print(f"{len(errors)} path header(s) do not name their own file:")
        for err in errors:
            print(f"  {err}")
        return 1
    print("check_path_headers: all path headers match their files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
