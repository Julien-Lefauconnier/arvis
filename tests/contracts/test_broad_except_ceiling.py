# tests/contracts/test_broad_except_ceiling.py
"""The number of broad exception handlers only goes down.

Campaign ONBOARD (audit #3 P2, 2026-09-03). Every ``except
Exception`` in the package is already policed for FORM by
``scripts/check_broad_excepts.py`` (it must route, re-raise or carry
a justification), but the audit's point stands: each broad handler
is a surface where a bug can dress up as controlled degradation, so
the COUNT deserves a ratchet too. The ceiling below is the measured
count on the day this test landed. Removing or narrowing a handler
lowers it in the same change; raising it is a deliberate act to be
argued in the pull request, exactly like any other ratchet.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARVIS = ROOT / "arvis"

# Measured 2026-09-03. Decrease-only in spirit: lower it when you
# remove a handler; never bump it to make one pass without argument.
BROAD_EXCEPT_CEILING = 155


def _broad_handler_count() -> int:
    count = 0
    for path in ARVIS.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ExceptHandler)
                and isinstance(node.type, ast.Name)
                and node.type.id == "Exception"
            ):
                count += 1
    return count


def test_broad_except_count_stays_under_the_ceiling() -> None:
    count = _broad_handler_count()
    assert count <= BROAD_EXCEPT_CEILING, (
        f"{count} broad except handlers against a ceiling of "
        f"{BROAD_EXCEPT_CEILING}: narrow the new one(s), or argue the "
        "raise explicitly in the change that needs it"
    )
    assert count >= 1, "the scan collapsed (zero handlers found)"


def test_the_ceiling_is_not_slack() -> None:
    """A ceiling far above the measured count is not a ratchet.

    Keeps the literal honest: when handlers are removed, the ceiling
    comes down in the same change (a slack of up to 5 is tolerated so
    unrelated work is not blocked mid-flight).
    """
    count = _broad_handler_count()
    assert BROAD_EXCEPT_CEILING - count <= 5, (
        f"ceiling {BROAD_EXCEPT_CEILING} is {BROAD_EXCEPT_CEILING - count} "
        "above the measured count; lower it to match"
    )
