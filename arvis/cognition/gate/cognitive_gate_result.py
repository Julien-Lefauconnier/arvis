# arvis/cognition/gate/cognitive_gate_result.py

from dataclasses import dataclass

from .cognitive_gate_verdict import CognitiveGateVerdict
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.cognition.gate.gate_decision_trace import GateDecisionTrace


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
        if verdict == LyapunovVerdict.ALLOW:
            cg_verdict = CognitiveGateVerdict.ALLOW
        elif verdict == LyapunovVerdict.REQUIRE_CONFIRMATION:
            cg_verdict = CognitiveGateVerdict.REQUIRE_CONFIRMATION
        elif verdict == LyapunovVerdict.ABSTAIN:
            cg_verdict = CognitiveGateVerdict.ABSTAIN
        else:
            cg_verdict = CognitiveGateVerdict.ABSTAIN

        normalized_codes = tuple(
            str(code).strip()
            for code in reason_codes
            if str(code).strip()
        )

        if not normalized_codes:
            normalized_codes = (f"lyapunov_{verdict.name.lower()}",)

        return cls(
            verdict=cg_verdict,
            reason_codes=normalized_codes,
            bundle_id=bundle_id,
            decision_trace=decision_trace,
        )