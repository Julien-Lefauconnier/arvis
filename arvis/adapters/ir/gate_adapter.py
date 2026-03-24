# aarvis/adapters/ir/gate_adapter.py

from __future__ import annotations

from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR


def _normalize_verdict(value: object | None) -> CognitiveGateVerdictIR:
    if value is None:
        return CognitiveGateVerdictIR.ABSTAIN

    raw = getattr(value, "value", value)
    raw_str = str(raw).strip().lower()

    if "." in raw_str:
        raw_str = raw_str.split(".")[-1]

    if raw_str not in {
        CognitiveGateVerdictIR.ALLOW.value,
        CognitiveGateVerdictIR.REQUIRE_CONFIRMATION.value,
        CognitiveGateVerdictIR.ABSTAIN.value,
    }:
        raw_str = CognitiveGateVerdictIR.ABSTAIN.value

    return CognitiveGateVerdictIR(raw_str)


def _normalize_reason_codes(gate: object) -> tuple[str, ...]:
    explicit_codes = getattr(gate, "reason_codes", None)
    if explicit_codes is not None:
        return tuple(str(x).strip() for x in explicit_codes if str(x).strip())

    reason = getattr(gate, "reason", "") or ""
    return tuple(part.strip() for part in str(reason).split("|") if part.strip())


class GateIRAdapter:
    @staticmethod
    def from_gate(gate: object) -> CognitiveGateIR:
        return CognitiveGateIR(
            verdict=_normalize_verdict(getattr(gate, "verdict", gate)),
            bundle_id=str(getattr(gate, "bundle_id", "")),
            reason_codes=_normalize_reason_codes(gate),
            risk_level=getattr(gate, "risk_level", None),
            triggered_rules=tuple(getattr(gate, "triggered_rules", ()) or ()),
        )