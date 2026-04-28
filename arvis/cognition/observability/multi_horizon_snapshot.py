# arvis/cognition/observability/multi_horizon_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class MultiHorizonSnapshot:
    collapse_risk: float
    stability_confidence: float
    early_warning: bool
    mode_hint: str | None = None
