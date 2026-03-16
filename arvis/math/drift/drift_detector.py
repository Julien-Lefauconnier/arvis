# arvis/math/drift/drift_detector.py

from dataclasses import dataclass


@dataclass(frozen=True)
class DriftSnapshot:
    drift_score: float
    regime: str


class DriftDetector:
    """
    ARVIS regime change detector.

    Based on contraction vs instability.
    """

    def evaluate(self, contraction_rate: float, instability_rate: float) -> DriftSnapshot:
        drift = instability_rate - contraction_rate

        regime = "STABLE"

        if drift > 0.4:
            regime = "CRITICAL"
        elif drift > 0.2:
            regime = "WARN"

        return DriftSnapshot(
            drift_score=drift,
            regime=regime,
        )