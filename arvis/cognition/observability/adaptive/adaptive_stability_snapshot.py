# arvis/cognition/observability/adaptive/adaptive_stability_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveStabilitySnapshot:
    kappa_eff: float | None
    switching_margin: float | None
    regime: str
    is_available: bool
