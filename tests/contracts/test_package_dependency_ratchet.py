# tests/contracts/test_package_dependency_ratchet.py
"""No new mutual dependency between top-level packages.

Campaign HARDEN (DM-H10, audit P2 cycles, 2026-09-02). The audit
counted 8 mutual package pairs (so "math is pure" is false today, and
kernel/adapters/cognition/tools lean on each other both ways). Each
pair is a design debt: resolving one is a deliberate refactoring act,
not a campaign side effect. This ratchet freezes the debt, dated: a
NEW mutual pair fails the gate immediately, and a pair that gets
resolved must leave the frozen list in the same change (so the debt
can only shrink).

The measure is static (ast imports), package-level (first path
segment under arvis/), and counts a pair once whatever the number of
modules involved.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

ARVIS = Path(__file__).resolve().parents[2] / "arvis"

# The frozen debt, observed at campaign HARDEN (2026-09-02, HEAD of
# the SURFACE campaign). Shrink-only: remove a pair when resolved,
# never add one.
KNOWN_MUTUAL_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("adapters", "kernel"),
        ("adapters", "kernel_core"),
        ("adapters", "tools"),
        ("cognition", "kernel"),
        ("cognition", "stability"),
        ("cognition", "uncertainty"),
        ("kernel", "tools"),
        ("kernel_core", "tools"),
    }
)


def _package_dependencies() -> dict[str, set[str]]:
    deps: dict[str, set[str]] = defaultdict(set)
    for path in ARVIS.rglob("*.py"):
        parts = path.relative_to(ARVIS).parts
        if len(parts) < 2:
            continue  # top-level modules belong to the root, skip
        source_package = parts[0]
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            for module in modules:
                if module.startswith("arvis."):
                    target = module.split(".")[1]
                    if target != source_package:
                        deps[source_package].add(target)
    return deps


def _mutual_pairs() -> set[tuple[str, str]]:
    deps = _package_dependencies()
    return {
        tuple(sorted((a, b))) for a in deps for b in deps[a] if a in deps.get(b, set())
    }


def test_no_new_mutual_package_pair() -> None:
    new = _mutual_pairs() - KNOWN_MUTUAL_PAIRS
    assert not new, (
        f"new mutual package dependency pair(s): {sorted(new)}. A cycle "
        "between top-level packages is a design decision, not a side "
        "effect: break the new back-edge instead of freezing it (DM-H10)."
    )


def test_resolved_pairs_leave_the_frozen_list() -> None:
    resolved = KNOWN_MUTUAL_PAIRS - _mutual_pairs()
    assert not resolved, (
        f"mutual pair(s) resolved: {sorted(resolved)}. Remove them from "
        "KNOWN_MUTUAL_PAIRS in the same change; the frozen debt only "
        "shrinks."
    )


def test_the_scan_is_not_vacuous() -> None:
    """The dependency scan sees the real graph (an empty result would
    make both ratchets pass trivially)."""
    deps = _package_dependencies()
    assert "kernel" in deps and deps["kernel"], deps.keys()
