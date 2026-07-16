# arvis/math/stability/hard_block_policy.py

"""Versioned severity table behind the stability envelope hard_block.

Audit F-003: the envelope carried a hard_block flag that was hardcoded
to False, leaving the downstream enforcement machinery dead and the
escalation semantics undefined. This module makes the mapping explicit,
versioned and testable.

Each stability reason is mapped to a severity:

- WARNING       observability only, never blocks.
- CONFIRMATION  the gate policy may require confirmation (its default
                behaviour for global instability).
- HARD_BLOCK    the envelope reports hard_block=True and the strict
                enforcement mode vetoes.

The default table maps no reason to HARD_BLOCK, which preserves the
pre-A5 runtime behaviour while making the policy explicit. Profiles
(lot B) may escalate reasons by passing their own table. An unknown
reason fails closed to HARD_BLOCK: a reason the table cannot classify
must not silently pass.

Pure math: no context, no side effects, no kernel imports.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum

HARD_BLOCK_TABLE_VERSION = "1"


class StabilitySeverity(StrEnum):
    WARNING = "warning"
    CONFIRMATION = "confirmation"
    HARD_BLOCK = "hard_block"


DEFAULT_SEVERITY_TABLE: dict[str, StabilitySeverity] = {
    "global": StabilitySeverity.CONFIRMATION,
    "switching": StabilitySeverity.WARNING,
    "exponential_bound": StabilitySeverity.CONFIRMATION,
}


def resolve_hard_block(
    reasons: Sequence[str],
    table: Mapping[str, StabilitySeverity] | None = None,
) -> tuple[bool, str | None]:
    """Resolve the envelope hard_block flag from stability reasons.

    Returns (hard_block, hard_reason). hard_reason keeps the historical
    underscore-joined encoding of all reasons for trace continuity.
    Unknown reasons fail closed to HARD_BLOCK.
    """
    severity_table = DEFAULT_SEVERITY_TABLE if table is None else table

    hard_block = any(
        severity_table.get(reason, StabilitySeverity.HARD_BLOCK)
        is StabilitySeverity.HARD_BLOCK
        for reason in reasons
    )
    hard_reason = "_".join(reasons) if reasons else None
    return hard_block, hard_reason


__all__ = [
    "HARD_BLOCK_TABLE_VERSION",
    "StabilitySeverity",
    "DEFAULT_SEVERITY_TABLE",
    "resolve_hard_block",
]
