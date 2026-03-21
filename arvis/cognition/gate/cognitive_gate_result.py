# arvis/cognition/gate/cognitive_gate_result.py

from dataclasses import dataclass
from .cognitive_gate_verdict import CognitiveGateVerdict
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


@dataclass(frozen=True)
class CognitiveGateResult:
    verdict: CognitiveGateVerdict
    reason: str | None
    bundle_id: str

    @classmethod
    def from_lyapunov(
        cls,
        verdict: LyapunovVerdict,
        bundle_id: str = "unknown",
        reason: str | None = None,
    ) -> "CognitiveGateResult":

        if verdict == LyapunovVerdict.ALLOW:
            cg_verdict = CognitiveGateVerdict.ALLOW

        elif verdict == LyapunovVerdict.REQUIRE_CONFIRMATION:
            cg_verdict = CognitiveGateVerdict.REQUIRE_CONFIRMATION

        elif verdict == LyapunovVerdict.ABSTAIN:
            cg_verdict = CognitiveGateVerdict.ABSTAIN

        else:
            cg_verdict = CognitiveGateVerdict.ABSTAIN

        return cls(
            verdict=cg_verdict,
            reason=reason or f"lyapunov:{verdict.name}",
            bundle_id=bundle_id,
        )