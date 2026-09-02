# arvis/stability/stability_snapshot.py

from dataclasses import dataclass

from arvis.math.observability.global_stability_snapshot import (
    GlobalStabilitySnapshot,
)


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

    reasons: list[str]

    @staticmethod
    def from_global(snapshot: GlobalStabilitySnapshot) -> "StabilitySnapshot":
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


# Campaign SURFACE (DM-S5, 2026-09-02): this module used to define a
# second, three-field StabilityView that nothing imported. The public
# stability view is arvis.api.stability.StabilityView; the duplicate
# (whose risk_level was the collapse_risk and whose "regime" was a
# verdict, both namings the audit flagged) is deleted.
