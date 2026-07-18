# arvis/tools/tool_result.py
"""Tool execution result with an explicit effect boundary (campaign 6).

The a8 audit (constat 11) showed a reserved confirmation was committed
whenever the executor returned, even when the failure happened BEFORE
the effect (schema violation, unknown tool, tool.validate refusal): a
legitimate human confirmation was burned for an effect that never ran.
The fix is an explicit classification of where the execution stopped,
carried by the result itself, so the manager commits the confirmation
only when the effect boundary was actually crossed and releases it on
any pre-effect refusal.
"""

from dataclasses import dataclass
from typing import Any

from arvis.errors.base import ArvisError

# Effect boundary classification (campaign 6, Lot 1, closes constat 11).
# PRE_EFFECT_REFUSAL: the tool body was never entered; no external
#   effect can have happened; a reserved confirmation is released.
# EFFECT_COMPLETED: the tool body ran to completion (even late, even
#   with an invalid output); the effect happened; commit.
# EFFECT_FAILED: the tool body was entered and raised; the effect may
#   have partially happened; commit (conservative: the confirmation is
#   considered spent once the boundary was crossed).
# EFFECT_UNKNOWN: legacy or unclassified paths; treated as crossed
#   (conservative).
PRE_EFFECT_REFUSAL = "pre_effect_refusal"
EFFECT_COMPLETED = "effect_completed"
EFFECT_FAILED = "effect_failed"
EFFECT_UNKNOWN = "effect_unknown"


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    success: bool
    output: Any | None = None
    error: ArvisError | None = None
    latency_ms: float | None = None
    # Where the execution stopped relative to the effect boundary; the
    # confirmation lifecycle keys on this, never on `success` alone.
    effect_boundary: str = EFFECT_UNKNOWN


__all__ = [
    "EFFECT_COMPLETED",
    "EFFECT_FAILED",
    "EFFECT_UNKNOWN",
    "PRE_EFFECT_REFUSAL",
    "ToolResult",
]
