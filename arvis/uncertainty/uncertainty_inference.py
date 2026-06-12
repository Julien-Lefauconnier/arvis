# arvis/uncertainty/uncertainty_inference.py
"""Deterministic decision-layer uncertainty producer (increments 1-2).

Consumes only ZK-safe perception features (no raw text) and emits declarative
:class:`ReasoningGap` / :class:`UncertaintyFrame` observations. Pure: no
decision, no execution, no backend coupling. Increment 1 covers referential
under-determination; increment 2 adds contextual under-determination (a
context-dependent query the kernel has no memory to resolve).
"""

from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass(frozen=True)
class UncertaintyInferenceResult:
    """Declarative uncertainty observations for one decision."""

    gaps: list[ReasoningGap] = field(default_factory=list)
    frames: list[UncertaintyFrame] = field(default_factory=list)


class UncertaintyInference:
    """Map ZK-safe perception features to uncertainty gaps/frames.

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
    ) -> UncertaintyInferenceResult:
        gaps: list[ReasoningGap] = []
        frames: list[UncertaintyFrame] = []
        if referential_ambiguity >= self._theta_ref:
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
        if context_dependent >= self._theta_ctx and not memory_present:
            gaps.append(
                ReasoningGap(
                    gap_type=GapType.MISSING_CONTEXT,
                    origin=GapOrigin.CONTEXT,
                    severity=GapSeverity.MEDIUM,
                    description="Query depends on context absent from memory.",
                )
            )
            frames.append(_CONTEXTUAL_FRAME)
        return UncertaintyInferenceResult(gaps=gaps, frames=frames)
