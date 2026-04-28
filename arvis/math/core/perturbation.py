# arvis/math/core/perturbation.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True)
class PerturbationSnapshot:
    """
    Paper-aligned perturbation term w_t
    """

    magnitude: float
    uncertainty: float
    drift: float
    risk: float
    symbolic: float

    def is_significant(self, threshold: float = 0.5) -> bool:
        return self.magnitude > threshold


def compute_perturbation(ctx: Any) -> Optional[PerturbationSnapshot]:
    try:
        uncertainty = float(getattr(ctx, "uncertainty", 0.0) or 0.0)
        drift = float(getattr(ctx, "drift_score", 0.0) or 0.0)
        risk = float(getattr(ctx, "collapse_risk", 0.0) or 0.0)

        symbolic = float(getattr(ctx, "symbolic_drift", 0.0) or 0.0)

        # Simple norm (L1-like)
        magnitude = abs(uncertainty) + abs(drift) + abs(risk) + abs(symbolic)

        return PerturbationSnapshot(
            magnitude=magnitude,
            uncertainty=uncertainty,
            drift=drift,
            risk=risk,
            symbolic=symbolic,
        )

    except Exception:
        return None
