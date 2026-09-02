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

        # DM-H7 (campaign HARDEN, audit P1-10): absence is typed, not
        # a sentinel. residual is None exactly when the projection
        # certified nothing this turn (DM-F3 designed absence) and
        # contributes no pressure; a NUMBER is a certified residual
        # and acts at face value, 1.0 (margin 0.0) being the worst.
        # The previous float-only code excluded residual >= 0.999 as
        # "no certification", which also switched the layer off on
        # the worst CERTIFIED state: margin 0.0 allowed while 0.05
        # abstained (the audit's probe).
        residual = w.projection_residual

        if (
            (residual is not None and residual > 0.7)
            or x.conflict_pressure > 0.8
            or z.dynamics.runtime_instability > 0.8
            or w.llm_risk_pressure > 0.9
        ):
            reasons.append("high_instability_or_projection_failure")

            if w.llm_risk_pressure > 0.9:
                reasons.append("critical_llm_risk")

            effective_residual = residual if residual is not None else 0.0

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

        # A None margin is designed absence (DM-F3): no low-margin
        # pressure. A certified margin below 0.3 is low, 0.0 included
        # (it normally already abstained above through its residual).
        effective_low_margin = margin is not None and margin < 0.3

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
