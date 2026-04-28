# arvis/stability/stability_snapshot.py

from dataclasses import dataclass
from typing import List, Any


@dataclass(frozen=True)
class StabilitySnapshot:
    """
    Public stability snapshot (OS-level contract).

    Stable, minimal, and decoupled from cognition internals.
    """

    verdict: str
    score: float
    confidence: float
    samples: int

    mean_dv: float
    std_dv: float
    instability_rate: float

    collapse_risk: float
    last_v: float

    reasons: List[str]

    @staticmethod
    def from_global(snapshot: Any) -> "StabilitySnapshot":
        """
        Adapter from internal GlobalStabilitySnapshot.
        """
        return StabilitySnapshot(
            verdict=snapshot.verdict,
            score=snapshot.score,
            confidence=snapshot.confidence,
            samples=snapshot.samples,
            mean_dv=snapshot.mean_dv,
            std_dv=snapshot.std_dv,
            instability_rate=snapshot.instability_rate,
            collapse_risk=snapshot.collapse_risk,
            last_v=snapshot.last_v,
            reasons=list(snapshot.reasons or []),
        )


@dataclass(frozen=True)
class StabilityView:
    stability_score: float
    risk_level: float
    regime: str

    @staticmethod
    def from_snapshot(s: StabilitySnapshot) -> "StabilityView":
        return StabilityView(
            stability_score=s.score,
            risk_level=s.collapse_risk,
            regime=s.verdict,
        )
