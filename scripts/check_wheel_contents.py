"""Reject repository-only or machine-generated files from ARVIS wheels."""

from __future__ import annotations

import sys
import zipfile
from pathlib import PurePosixPath

_FORBIDDEN_PARTS = {
    ".DS_Store",
    ".coverage",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "Thumbs.db",
    "__pycache__",
}
_FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}


def _forbidden_entry(name: str) -> bool:
    path = PurePosixPath(name)
    parts = path.parts
    if any(part in _FORBIDDEN_PARTS for part in parts):
        return True
    if path.suffix in _FORBIDDEN_SUFFIXES:
        return True
    return bool(parts and parts[0] == "tests")


def main(wheel_names: list[str]) -> int:
    if not wheel_names:
        print("usage: check_wheel_contents.py WHEEL [WHEEL ...]", file=sys.stderr)
        return 2

    failures: list[tuple[str, str]] = []
    for wheel_name in wheel_names:
        with zipfile.ZipFile(wheel_name) as wheel:
            failures.extend(
                (wheel_name, name)
                for name in wheel.namelist()
                if _forbidden_entry(name)
            )

    if failures:
        for wheel_name, name in failures:
            print(f"forbidden wheel entry: {wheel_name}: {name}", file=sys.stderr)
        return 1

    print(f"wheel content check passed: {len(wheel_names)} artifact(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
