# arvis/cognition/gate/cognitive_gate_result.py

from dataclasses import dataclass

from arvis.cognition.gate.gate_decision_trace import GateDecisionTrace
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

from .cognitive_gate_verdict import CognitiveGateVerdict


@dataclass(frozen=True)
class CognitiveGateResult:
    verdict: CognitiveGateVerdict
    reason_codes: tuple[str, ...]
    bundle_id: str
    decision_trace: GateDecisionTrace | None = None

    @classmethod
    def from_lyapunov(
        cls,
        verdict: LyapunovVerdict,
        bundle_id: str = "unknown",
        reason_codes: tuple[str, ...] = (),
        decision_trace: GateDecisionTrace | None = None,
    ) -> "CognitiveGateResult":
        # Total, fail-closed conversion owned by the enum (campaign
        # SURFACE, DM-S5): unknown inputs map to ABSTAIN, never ALLOW.
        cg_verdict = CognitiveGateVerdict.from_lyapunov(verdict)

        normalized_codes = tuple(
            str(code).strip() for code in reason_codes if str(code).strip()
        )

        if not normalized_codes:
            normalized_codes = (f"lyapunov_{verdict.name.lower()}",)

        return cls(
            verdict=cg_verdict,
            reason_codes=normalized_codes,
            bundle_id=bundle_id,
            decision_trace=decision_trace,
        )
