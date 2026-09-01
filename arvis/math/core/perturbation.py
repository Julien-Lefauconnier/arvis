# arvis/math/core/perturbation.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


def compute_perturbation(ctx: Any) -> PerturbationSnapshot | None:
    try:
        # Canonical sub-context reads with math-layer duck tolerance
        # (campaign OBS, LOT O4: the root facade mirrors are gone; the
        # math layer stays import-free of the kernel by chaining).
        core = getattr(getattr(ctx, "scientific", None), "core", None)
        observability = getattr(ctx, "observability", None)
        symbolic_ctx = getattr(observability, "symbolic", None)

        uncertainty = float(getattr(core, "uncertainty", 0.0) or 0.0)
        drift = float(getattr(core, "drift_score", 0.0) or 0.0)
        risk = float(getattr(core, "collapse_risk", 0.0) or 0.0)

        symbolic = float(getattr(symbolic_ctx, "symbolic_drift", 0.0) or 0.0)

        # Simple norm (L1-like)
        magnitude = abs(uncertainty) + abs(drift) + abs(risk) + abs(symbolic)

        return PerturbationSnapshot(
            magnitude=magnitude,
            uncertainty=uncertainty,
            drift=drift,
            risk=risk,
            symbolic=symbolic,
        )

    except (TypeError, ValueError, OverflowError):
        return None
