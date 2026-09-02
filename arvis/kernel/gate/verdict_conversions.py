# arvis/kernel/gate/verdict_conversions.py

"""Typed, total conversions between the gate verdict vocabularies.

Campaign SURFACE (DM-S5, 2026-09-02). The kernel boundary speaks two
verdict vocabularies: ``LyapunovVerdict`` (the governed verdict of the
decision stack, uppercase wire values) and ``CognitiveGateVerdictIR``
(the IR artifact vocabulary, lowercase wire values, part of canonical
bytes). Before this module, the conversions between them lived as
scattered string comparisons on ``.value`` with an implicit fail-open
else branch. Every conversion is now a total mapping in one place:
exhaustive over the enum members (a table test locks both directions)
and fail-closed on anything else. No wire value changes.
"""

from __future__ import annotations

from arvis.ir.gate import CognitiveGateVerdictIR
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

GATE_IR_TO_LYAPUNOV: dict[CognitiveGateVerdictIR, LyapunovVerdict] = {
    CognitiveGateVerdictIR.ALLOW: LyapunovVerdict.ALLOW,
    CognitiveGateVerdictIR.REQUIRE_CONFIRMATION: (LyapunovVerdict.REQUIRE_CONFIRMATION),
    CognitiveGateVerdictIR.ABSTAIN: LyapunovVerdict.ABSTAIN,
}

LYAPUNOV_TO_GATE_IR: dict[LyapunovVerdict, CognitiveGateVerdictIR] = {
    lyapunov: gate_ir for gate_ir, lyapunov in GATE_IR_TO_LYAPUNOV.items()
}


def lyapunov_from_gate_ir(verdict: CognitiveGateVerdictIR) -> LyapunovVerdict:
    """Map an IR gate verdict to the governed verdict vocabulary.

    Total over the enum; anything that is not a member maps to
    ABSTAIN (fail-closed), never to ALLOW.
    """
    return GATE_IR_TO_LYAPUNOV.get(verdict, LyapunovVerdict.ABSTAIN)


def gate_ir_from_lyapunov(verdict: LyapunovVerdict) -> CognitiveGateVerdictIR:
    """Map a governed verdict to the IR artifact vocabulary.

    Total over the enum; anything that is not a member maps to
    ABSTAIN (fail-closed), never to ALLOW.
    """
    return LYAPUNOV_TO_GATE_IR.get(verdict, CognitiveGateVerdictIR.ABSTAIN)


def parse_gate_verdict_wire(value: object) -> CognitiveGateVerdictIR:
    """Parse a wire-format gate verdict string into the IR enum.

    The Z-gate layer carries its verdict as a plain string; unknown or
    non-string values parse to ABSTAIN (fail-closed), preserving the
    behavior of the else branches this parser replaces.
    """
    if isinstance(value, CognitiveGateVerdictIR):
        return value
    if isinstance(value, str):
        try:
            return CognitiveGateVerdictIR(value)
        except ValueError:
            return CognitiveGateVerdictIR.ABSTAIN
    return CognitiveGateVerdictIR.ABSTAIN
