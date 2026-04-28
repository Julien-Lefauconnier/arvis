# arvis/kernel/gate/pi_gate.py

from __future__ import annotations

from arvis.kernel.projection.pi_types import PiState
from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR


class PiBasedGate:
    """
    Gate driven purely by Π structured state.
    ZKCS-compliant decision layer.
    """

    def evaluate(self, pi: PiState, bundle_id: str) -> CognitiveGateIR:
        z = pi.z
        w = pi.w
        x = pi.x

        reasons = []

        # =========================================
        # 0. BASE VERDICT FROM Π
        # =========================================
        base_verdict = z.gate.verdict

        # =========================================
        # 1. HARD SAFETY (ABSTAIN)
        # =========================================

        # NOTE:
        # residual == 1.0 can mean "no certification available"
        # → do NOT treat as hard failure (intermediate phase)
        residual = w.projection_residual

        if (
            (residual > 0.7 and residual < 0.999)
            or x.conflict_pressure > 0.8
            or z.dynamics.runtime_instability > 0.8
        ):
            reasons.append("high_instability_or_projection_failure")

            return CognitiveGateIR(
                verdict=CognitiveGateVerdictIR.ABSTAIN,
                bundle_id=bundle_id,
                reason_codes=tuple(reasons),
                risk_level=max(
                    w.projection_residual,
                    x.conflict_pressure,
                    z.dynamics.runtime_instability,
                ),
            )

        # =========================================
        # 2. CONFIRMATION ZONE (override allow only)
        # =========================================

        margin = z.gate.safety_margin

        # NOTE:
        # margin == 0.0 may mean "no certification available"
        # → do NOT treat as low margin
        effective_low_margin = margin < 0.3 and margin > 0.0

        if base_verdict == "allow" and (
            w.uncertainty_pressure > 0.6
            or effective_low_margin
            or x.uncertainty_mass > 0.6
        ):
            reasons.append("uncertainty_or_low_margin")

            return CognitiveGateIR(
                verdict=CognitiveGateVerdictIR.REQUIRE_CONFIRMATION,
                bundle_id=bundle_id,
                reason_codes=tuple(reasons),
                risk_level=w.uncertainty_pressure,
            )

        # =========================================
        # 3. SAFE EXECUTION
        # =========================================

        reasons.append("pi_decision")

        if base_verdict == "require_confirmation":
            verdict = CognitiveGateVerdictIR.REQUIRE_CONFIRMATION
        elif base_verdict == "allow":
            verdict = CognitiveGateVerdictIR.ALLOW
        else:
            verdict = CognitiveGateVerdictIR.ABSTAIN

        return CognitiveGateIR(
            verdict=verdict,
            bundle_id=bundle_id,
            reason_codes=tuple(reasons),
            risk_level=w.uncertainty_pressure,
        )
