# arvis/uncertainty/uncertainty_inference.py
"""Deterministic decision-layer uncertainty producer (increments 1-3).

Consumes only ZK-safe perception features (no raw text) plus the kernel's own
intent, and emits declarative :class:`ReasoningGap` / :class:`UncertaintyFrame`
/ :class:`ConflictSignal` observations. Pure: no decision, no execution, no
backend coupling. Increment 1 covers referential under-determination; increment
2 adds contextual under-determination (a context-dependent query the kernel has
no memory to resolve); increment 3 adds internal conflict (an action request
whose target is under-determined): kernel-computed, orthogonal to grounding.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from arvis.cognition.conflict.conflict_signal import ConflictSignal
from arvis.cognition.conflict.conflict_type import REASON_MISMATCH
from arvis.reasoning.reasoning_gap import (
    GapOrigin,
    GapSeverity,
    GapType,
    ReasoningGap,
)
from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame

_REFERENTIAL_FRAME = UncertaintyFrame(
    frame_id="REFERENTIAL",
    label="Referential ambiguity",
    description="The query referent is under-determined by available context.",
    axes={UncertaintyAxis.AMBIGUOUS_REFERENCE},
)
_CONTEXTUAL_FRAME = UncertaintyFrame(
    frame_id="CONTEXTUAL",
    label="Missing context",
    description="The query depends on context the kernel has no memory to supply.",
    axes={UncertaintyAxis.CONTEXT_DEPENDENT},
)
_CONFLICT_FRAME = UncertaintyFrame(
    frame_id="INTERNAL_CONFLICT",
    label="Internal signal conflict",
    description="An action is requested on an under-determined target.",
    axes={UncertaintyAxis.INTERNAL_CONFLICT},
)


@dataclass(frozen=True)
class UncertaintyInferenceResult:
    """Declarative uncertainty observations for one decision."""

    gaps: list[ReasoningGap] = field(default_factory=list)
    frames: list[UncertaintyFrame] = field(default_factory=list)
    conflicts: list[ConflictSignal] = field(default_factory=list)


class UncertaintyInference:
    """Map ZK-safe perception features + intent to uncertainty observations.

    ``theta_ref`` / ``theta_ctx`` are the referential / contextual firing
    thresholds (calibratable).
    """

    def __init__(self, theta_ref: float = 0.5, theta_ctx: float = 0.5) -> None:
        if not (0.0 <= theta_ref <= 1.0):
            raise ValueError("theta_ref must be in [0, 1]")
        if not (0.0 <= theta_ctx <= 1.0):
            raise ValueError("theta_ctx must be in [0, 1]")
        self._theta_ref = theta_ref
        self._theta_ctx = theta_ctx

    def infer(
        self,
        *,
        referential_ambiguity: float = 0.0,
        context_dependent: float = 0.0,
        memory_present: bool = True,
        reason: str = "",
    ) -> UncertaintyInferenceResult:
        gaps: list[ReasoningGap] = []
        frames: list[UncertaintyFrame] = []
        conflicts: list[ConflictSignal] = []
        referential_under = referential_ambiguity >= self._theta_ref
        context_under = context_dependent >= self._theta_ctx and not memory_present
        if referential_under:
            gaps.append(
                ReasoningGap(
                    gap_type=GapType.AMBIGUOUS_INTENT,
                    origin=GapOrigin.USER,
                    severity=GapSeverity.MEDIUM,
                    description="Query referent under-determined.",
                )
            )
            frames.append(_REFERENTIAL_FRAME)
        # Contextual: the conjunction is the gap. A context-dependent query
        # whose context memory CAN supply is resolved => no gap.
        if context_under:
            gaps.append(
                ReasoningGap(
                    gap_type=GapType.MISSING_CONTEXT,
                    origin=GapOrigin.CONTEXT,
                    severity=GapSeverity.MEDIUM,
                    description="Query depends on context absent from memory.",
                )
            )
            frames.append(_CONTEXTUAL_FRAME)
        # Internal conflict: an action request on an under-determined target.
        # Orthogonal to grounding: fires even when retrieval is strong.
        if reason == "action_request" and (referential_under or context_under):
            conflicts.append(
                ConflictSignal(type=REASON_MISMATCH, payload={"reason": reason})
            )
            frames.append(_CONFLICT_FRAME)
        return UncertaintyInferenceResult(gaps=gaps, frames=frames, conflicts=conflicts)
