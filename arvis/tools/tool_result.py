# arvis/tools/tool_result.py
"""Tool execution result with an explicit effect lifecycle.

Campaign 7 Lot 5 distinguishes every materially different point around the
external-effect boundary. Confirmation finalization must never infer this from
``success`` alone: a refusal or internal failure before the tool body releases
the reservation, while any state at or beyond the effect boundary spends it
conservatively.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from arvis.errors.base import ArvisError


class ToolEffectState(StrEnum):
    """Where execution stopped relative to the external-effect boundary."""

    PRE_EFFECT_REFUSAL = "pre_effect_refusal"
    EFFECT_NOT_STARTED = "effect_not_started"
    EFFECT_STARTED = "effect_started"
    EFFECT_COMPLETED = "effect_completed"
    EFFECT_FAILED = "effect_failed"
    EFFECT_STATE_UNKNOWN = "effect_state_unknown"
    # Persisted pre-Campaign-7 value kept as a conservative legacy state.
    EFFECT_UNKNOWN = "effect_unknown"


# Backward-compatible module constants. StrEnum preserves string comparison
# semantics for hosts that persisted the former string values.
PRE_EFFECT_REFUSAL = ToolEffectState.PRE_EFFECT_REFUSAL
EFFECT_NOT_STARTED = ToolEffectState.EFFECT_NOT_STARTED
EFFECT_STARTED = ToolEffectState.EFFECT_STARTED
EFFECT_COMPLETED = ToolEffectState.EFFECT_COMPLETED
EFFECT_FAILED = ToolEffectState.EFFECT_FAILED
EFFECT_STATE_UNKNOWN = ToolEffectState.EFFECT_STATE_UNKNOWN
# Historical name and value retained for persisted hosts. New results use the
# explicit EFFECT_STATE_UNKNOWN state.
EFFECT_UNKNOWN = ToolEffectState.EFFECT_UNKNOWN


def effect_has_started(state: ToolEffectState | str) -> bool:
    """Return whether a confirmation must be considered spent.

    Unknown states are conservative: once ARVIS cannot prove the effect did not
    start, it must not make a human confirmation reusable.
    """

    try:
        normalized = ToolEffectState(state)
    except ValueError:
        return True
    return normalized not in {
        ToolEffectState.PRE_EFFECT_REFUSAL,
        ToolEffectState.EFFECT_NOT_STARTED,
    }


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    success: bool
    output: Any | None = None
    error: ArvisError | None = None
    latency_ms: float | None = None
    # Where execution stopped relative to the effect boundary; confirmation
    # lifecycle keys on this field, never on ``success`` alone.
    effect_boundary: ToolEffectState | str = EFFECT_STATE_UNKNOWN

    def __post_init__(self) -> None:
        try:
            normalized = ToolEffectState(self.effect_boundary)
        except ValueError:
            # A foreign/legacy state is retained as unknown rather than trusted
            # as pre-effect. This is deliberately conservative.
            normalized = EFFECT_STATE_UNKNOWN
        object.__setattr__(self, "effect_boundary", normalized)


__all__ = [
    "EFFECT_COMPLETED",
    "EFFECT_FAILED",
    "EFFECT_NOT_STARTED",
    "EFFECT_STARTED",
    "EFFECT_STATE_UNKNOWN",
    "EFFECT_UNKNOWN",
    "PRE_EFFECT_REFUSAL",
    "ToolEffectState",
    "ToolResult",
    "effect_has_started",
]
