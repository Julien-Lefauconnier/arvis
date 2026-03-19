# arvis/cognition/control/temporal_regulation.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemporalModulation:
    risk_multiplier: float = 1.0
    epsilon_multiplier: float = 1.0


class TemporalRegulation:
    """
    Kernel-safe temporal modulation.

    Requires pre-computed timeline summary input.
    """

    def compute(
        self,
        *,
        total: int,
        has_conflicts: bool,
        has_gaps: bool,
        has_uncertainty: bool,
        healthy: bool,
    ) -> TemporalModulation:

        base = min(1.0, total / 100.0)

        conflict_penalty = 0.10 if has_conflicts else 0.0
        gap_penalty = 0.05 if has_gaps else 0.0
        uncertainty_penalty = 0.05 if has_uncertainty else 0.0
        structural_penalty = 0.10 if not healthy else 0.0

        stability = max(
            0.0,
            base - conflict_penalty - gap_penalty - uncertainty_penalty - structural_penalty,
        )

        risk_multiplier = 1.0 + (1.0 - stability) * 0.30
        epsilon_multiplier = 1.0 - stability * 0.20

        return TemporalModulation(
            risk_multiplier=float(risk_multiplier),
            epsilon_multiplier=float(epsilon_multiplier),
        )