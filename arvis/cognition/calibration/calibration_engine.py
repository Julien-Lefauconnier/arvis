# arvis/cognition/calibration/calibration_engine.py

from dataclasses import dataclass
from enum import StrEnum

from arvis.cognition.policy.cognitive_policy_result import CognitivePolicyResult


class CalibrationRegime(StrEnum):
    STABLE = "stable"
    UNSTABLE = "unstable"
    DRIFTING = "drifting"
    REGIME_SHIFT = "regime_shift"


@dataclass
class CalibrationSnapshot:
    contraction_rate: float
    instability_rate: float
    drift_score: float | None
    collapse_risk: float | None
    regime: CalibrationRegime


class CalibrationEngine:
    """
    Cognitive calibration evaluator.

    - Pure
    - Stateless
    - Emits optional CognitivePolicyResult suggestions
    """

    def evaluate(
        self,
        *,
        contraction_rate: float | None,
        instability_rate: float | None,
        drift_score: float | None = None,
        collapse_risk: float | None = None,
    ) -> tuple[
        CalibrationSnapshot | None,
        list[CognitivePolicyResult] | None,
    ]:
        if contraction_rate is None or instability_rate is None:
            return None, None

        # -------------------------
        # Determine regime
        # -------------------------
        regime = CalibrationRegime.STABLE

        if instability_rate > 0.3:
            regime = CalibrationRegime.UNSTABLE
        elif contraction_rate < 0.2:
            regime = CalibrationRegime.DRIFTING

        if drift_score is not None and drift_score > 0.7:
            regime = CalibrationRegime.REGIME_SHIFT

        snapshot = CalibrationSnapshot(
            contraction_rate=contraction_rate,
            instability_rate=instability_rate,
            drift_score=drift_score,
            collapse_risk=collapse_risk,
            regime=regime,
        )

        # -------------------------
        # Optional policy emission
        # -------------------------
        policies: list[CognitivePolicyResult] = []

        if regime == CalibrationRegime.UNSTABLE:
            policies.append(
                CognitivePolicyResult(
                    policy_name="calibration.stability_guard",
                    dimension="stability",
                    suggestion_type="reduce_exploration",
                    rationale="System instability detected",
                )
            )

        elif regime == CalibrationRegime.DRIFTING:
            policies.append(
                CognitivePolicyResult(
                    policy_name="calibration.drift_guard",
                    dimension="stability",
                    suggestion_type="increase_observation",
                    rationale="System drift detected",
                )
            )

        elif regime == CalibrationRegime.REGIME_SHIFT:
            policies.append(
                CognitivePolicyResult(
                    policy_name="calibration.regime_shift",
                    dimension="stability",
                    suggestion_type="recalibrate",
                    rationale="Significant regime change detected",
                )
            )

        return snapshot, (policies or None)
