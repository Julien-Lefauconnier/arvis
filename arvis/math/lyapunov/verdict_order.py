# arvis/math/lyapunov/verdict_order.py

"""Canonical strictness order over gate verdicts (audit F-001).

The safety rule of the enforcement phase of the gate stack is:

    ALLOW < REQUIRE_CONFIRMATION < ABSTAIN

A stage may harden the verdict, never relax it. This module is the
single production-code source of that order; the gate stack composes
verdicts through it instead of re-deriving comparisons locally.

Pure math: no context, no side effects, no kernel imports.
"""

from __future__ import annotations

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

VERDICT_STRICTNESS: dict[LyapunovVerdict, int] = {
    LyapunovVerdict.ALLOW: 0,
    LyapunovVerdict.REQUIRE_CONFIRMATION: 1,
    LyapunovVerdict.ABSTAIN: 2,
}


def strictness(verdict: LyapunovVerdict) -> int:
    """Rank of a verdict in the canonical strictness order."""
    return VERDICT_STRICTNESS[verdict]


def max_strictness(
    first: LyapunovVerdict,
    second: LyapunovVerdict,
) -> LyapunovVerdict:
    """Monotone composition: the stricter of two verdicts wins."""
    return first if strictness(first) >= strictness(second) else second


def is_relaxation(
    before: LyapunovVerdict,
    after: LyapunovVerdict,
) -> bool:
    """Whether moving from ``before`` to ``after`` weakens the verdict."""
    return strictness(after) < strictness(before)


__all__ = [
    "VERDICT_STRICTNESS",
    "strictness",
    "max_strictness",
    "is_relaxation",
]
