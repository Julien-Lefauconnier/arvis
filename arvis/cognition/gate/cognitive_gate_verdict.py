# arvis/cognition/gate/cognitive_gate_verdict.py

from __future__ import annotations

from enum import StrEnum

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class CognitiveGateVerdict(StrEnum):
    ALLOW = "allow"
    REQUIRE_CONFIRMATION = "require_confirmation"
    ABSTAIN = "abstain"

    @classmethod
    def from_lyapunov(cls, verdict: LyapunovVerdict) -> CognitiveGateVerdict:
        """Total mapping from the governed verdict vocabulary.

        Campaign SURFACE (DM-S5, 2026-09-02): the conversion this enum
        owns, replacing an if chain; anything that is not a
        ``LyapunovVerdict`` member maps to ABSTAIN (fail-closed),
        never to ALLOW. No wire value changes.
        """
        return _FROM_LYAPUNOV.get(verdict, cls.ABSTAIN)


_FROM_LYAPUNOV: dict[LyapunovVerdict, CognitiveGateVerdict] = {
    LyapunovVerdict.ALLOW: CognitiveGateVerdict.ALLOW,
    LyapunovVerdict.REQUIRE_CONFIRMATION: (CognitiveGateVerdict.REQUIRE_CONFIRMATION),
    LyapunovVerdict.ABSTAIN: CognitiveGateVerdict.ABSTAIN,
}
