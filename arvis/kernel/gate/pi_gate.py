# arvis/kernel/gate/pi_gate.py

from __future__ import annotations

from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR
from arvis.kernel.gate.verdict_conversions import parse_gate_verdict_wire
from arvis.kernel.projection.pi_types import PiState


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
        # Wire string parsed once, fail-closed (campaign SURFACE,
        # DM-S5): an unknown value is ABSTAIN, as the else branches
        # below always treated it.
        base_verdict = parse_gate_verdict_wire(z.gate.verdict)

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
            or w.llm_risk_pressure > 0.9
        ):
            reasons.append("high_instability_or_projection_failure")

            if w.llm_risk_pressure > 0.9:
                reasons.append("critical_llm_risk")

            # NOTE:
            # residual == 1.0 may represent
            # "projection uncertified / unavailable"
            # and MUST NOT dominate runtime risk.
            effective_residual = (
                0.0 if w.projection_residual >= 0.999 else w.projection_residual
            )

            return CognitiveGateIR(
                verdict=CognitiveGateVerdictIR.ABSTAIN,
                bundle_id=bundle_id,
                reason_codes=tuple(reasons),
                risk_level=max(
                    effective_residual,
                    x.conflict_pressure,
                    z.dynamics.runtime_instability,
                    w.llm_risk_pressure,
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

        if base_verdict is CognitiveGateVerdictIR.ALLOW and (
            w.uncertainty_pressure > 0.6
            or effective_low_margin
            or x.uncertainty_mass > 0.6
            or w.llm_risk_pressure > 0.45
        ):
            reasons.append("uncertainty_or_low_margin")

            if w.llm_risk_pressure > 0.45:
                reasons.append("elevated_llm_risk")

            return CognitiveGateIR(
                verdict=CognitiveGateVerdictIR.REQUIRE_CONFIRMATION,
                bundle_id=bundle_id,
                reason_codes=tuple(reasons),
                risk_level=max(
                    w.uncertainty_pressure,
                    w.llm_risk_pressure,
                ),
            )

        # =========================================
        # 3. SAFE EXECUTION
        # =========================================

        reasons.append("pi_decision")

        verdict = base_verdict

        return CognitiveGateIR(
            verdict=verdict,
            bundle_id=bundle_id,
            reason_codes=tuple(reasons),
            risk_level=max(
                w.uncertainty_pressure,
                w.llm_risk_pressure,
            ),
        )
