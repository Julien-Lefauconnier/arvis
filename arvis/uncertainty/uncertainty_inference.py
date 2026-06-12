# arvis/uncertainty/uncertainty_inference.py
"""Deterministic decision-layer uncertainty producer (increment 1).

Consumes only ZK-safe perception features (no raw text) and emits declarative
:class:`ReasoningGap` / :class:`UncertaintyFrame` observations. Pure: no
decision, no execution, no backend coupling. Increment 1 covers referential
under-determination; contextual and conflict sources extend the same producer.
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


@dataclass(frozen=True)
class UncertaintyInferenceResult:
    """Declarative uncertainty observations for one decision."""

    gaps: list[ReasoningGap] = field(default_factory=list)
    frames: list[UncertaintyFrame] = field(default_factory=list)


class UncertaintyInference:
    """Map ZK-safe perception features to uncertainty gaps/frames.

    ``theta_ref`` is the referential-ambiguity firing threshold (calibratable).
    """

    def __init__(self, theta_ref: float = 0.5) -> None:
        if not (0.0 <= theta_ref <= 1.0):
            raise ValueError("theta_ref must be in [0, 1]")
        self._theta_ref = theta_ref

    def infer(self, *, referential_ambiguity: float) -> UncertaintyInferenceResult:
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
        return UncertaintyInferenceResult(gaps=gaps, frames=frames)
