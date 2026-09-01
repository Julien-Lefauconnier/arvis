#!/usr/bin/env python3
# scripts/check_broad_excepts.py
"""Gate ratchet: every ``except Exception`` handler must do something
honest with the exception (campaign FIX, LOT F2).

The two structurally dead layers of the MATH campaigns survived
behind silent degradation; the audit that followed classified all
broad handlers and found them sound. This checker keeps it that way:
a handler is accepted when it

- carries an ``# arvis-broad: <reason>`` annotation on its line, or
- re-raises (any ``raise`` in its body), or
- visibly routes the failure: captures or attaches it (ErrorManager
  and friends), records or logs it, emits it, normalizes it, or
  returns a typed failure value.

A bare swallower (``pass``, ``return None``, silent fallback) fails
the gate and must either be narrowed, made to route the failure, or
annotated with a justification.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_ROUTING_MARKERS = (
    "ErrorManager",
    "capture",
    "attach",
    "_record_error",
    "record_",
    "logger",
    "logging",
    "emit_error",
    "_emit_error",
    "failure",
    "Failure",
    "normalize_error",
    "ProviderAttempt",
    "revoke",
)


def _handler_ok(src: str, node: ast.ExceptHandler, line: str) -> bool:
    if "arvis-broad" in line:
        return True
    for sub in ast.walk(node):
        if isinstance(sub, ast.Raise):
            return True
    body_src = ast.get_source_segment(src, node) or ""
    return any(marker in body_src for marker in _ROUTING_MARKERS)


def check(paths: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in paths:
        src = path.read_text()
        lines = src.splitlines()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            if not (isinstance(node.type, ast.Name) and node.type.id == "Exception"):
                continue
            if not _handler_ok(src, node, lines[node.lineno - 1]):
                shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
                violations.append(
                    f"{shown}:{node.lineno}: broad except "
                    "swallows silently; narrow it, route the failure, or "
                    "annotate with '# arvis-broad: <reason>'"
                )
    return violations


def main() -> int:
    violations = check(sorted((ROOT / "arvis").rglob("*.py")))
    if violations:
        print(f"{len(violations)} silent broad except(s):")
        for v in violations:
            print(f"  {v}")
        return 1
    print("check_broad_excepts: every broad except routes its failure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
