# tests/contracts/test_broad_except_guard.py
"""Ratchet guard: broad exception handlers must be classified.

A broad handler (``except Exception``, ``except BaseException`` or a bare
``except``) is COMPLIANT when it does one of:

  C1. re-raise, or construct a typed error (a call whose name ends with
      ``Error`` or ``Violation``, or ``SyscallResult.failure``);
  C2. route through the sanctioned error machinery (``ErrorManager``
      methods, the syscall handler failure helpers, an error hook);
  C3. carry the normalized justification marker on the ``except`` line:
      ``# arvis-broad: <reason>`` (a deliberate, documented isolation
      boundary).

The ratchet has two teeth:
  - zones listed in TREATED_ZONES must have ZERO non-compliant handlers;
  - the total count of non-compliant handlers in the remaining zones must
    not exceed UNTREATED_CEILING (lowered as the A1 campaign progresses,
    zone by zone, until every zone is treated and the ceiling reaches 0).

A zone is the first path segment under ``arvis/`` (``kernel``,
``cognition``, ``math``...). When a zone is cleaned, add it to
TREATED_ZONES and lower UNTREATED_CEILING to the measured remainder.
"""

from __future__ import annotations

import ast
from pathlib import Path

BROAD = {"Exception", "BaseException"}

# C2: sanctioned routing calls (method or function names).
SANCTIONED_CALLS = {
    # ErrorManager surface
    "capture_exception",
    "normalize_for_boundary",
    "attach",
    # syscall handler failure helpers (route through normalize_error)
    "_failure_from_exception",
    "_failure_from_error",
    # typed syscall failure constructor
    "failure",
    # runtime hook isolation
    "_emit_error",
    # taxonomy entry point (ErrorManager.normalize / provider fallback)
    "normalize_error",
}

MARKER = "# arvis-broad:"

# Zones fully classified by the A1 campaign (ratchet tooth 1).
TREATED_ZONES = frozenset(
    {"adapters", "api", "ir", "kernel_core", "math", "stability", "telemetry", "tools"}
)

# Non-compliant handlers tolerated in the not-yet-treated zones
# (ratchet tooth 2). Lower this with every A1 lot; target is 0.
UNTREATED_CEILING = 82


def _catches_broad(handler: ast.ExceptHandler) -> bool:
    node = handler.type
    if node is None:
        return True
    if isinstance(node, ast.Name):
        return node.id in BROAD
    if isinstance(node, ast.Tuple):
        return any(isinstance(elt, ast.Name) and elt.id in BROAD for elt in node.elts)
    return False


def _is_compliant(handler: ast.ExceptHandler, source_lines: list[str]) -> bool:
    if MARKER in source_lines[handler.lineno - 1]:
        return True
    for node in ast.walk(handler):
        if isinstance(node, ast.Raise):
            return True
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            if name in SANCTIONED_CALLS:
                return True
            if name.endswith("Error") or name.endswith("Violation"):
                return True
    return False


def _zone(path: Path) -> str:
    parts = path.parts
    return parts[1] if len(parts) > 2 else parts[-1]


def test_broad_except_handlers_are_classified() -> None:
    root = Path("arvis")

    treated_offenders: list[str] = []
    untreated_count = 0

    for path in sorted(root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                if not _catches_broad(handler):
                    continue
                if _is_compliant(handler, source_lines):
                    continue
                if _zone(path) in TREATED_ZONES:
                    treated_offenders.append(f"{path}:{handler.lineno}")
                else:
                    untreated_count += 1

    assert treated_offenders == [], (
        "Non-compliant broad except in a treated zone (type it, route it "
        f"through the error machinery, or mark it '{MARKER} <reason>'): "
        f"{treated_offenders}"
    )
    assert untreated_count <= UNTREATED_CEILING, (
        f"Broad-except debt grew in untreated zones: {untreated_count} > "
        f"{UNTREATED_CEILING}. New broad handlers must be compliant."
    )
