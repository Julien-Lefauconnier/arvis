# arvis/adapters/ir/gate_adapter.py

from __future__ import annotations

from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR, CognitiveGateTraceStepIR



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
    return tuple(getattr(gate, "reason_codes", ()) or ())

def _map_trace(gate: object) -> tuple[CognitiveGateTraceStepIR, ...]:
    trace = getattr(gate, "decision_trace", None)
    if trace is None:
        return ()

    steps = getattr(trace, "steps", None)
    if not steps:
        return ()

    return tuple(
        CognitiveGateTraceStepIR(
            stage=s.stage,
            before=s.before,
            after=s.after,
            reason_codes=s.reason_codes,
            severity=getattr(s, "severity", 0.0),
            stability_impact=getattr(s, "stability_impact", 0.0),
        )
        for s in steps
    )

def _extract_trace_metrics(gate: object) -> tuple[float | None, float | None, float | None]:
    trace = getattr(gate, "decision_trace", None)
    if trace is None:
        return None, None, None

    return (
        getattr(trace, "total_severity", None),
        getattr(trace, "max_severity", None),
        getattr(trace, "instability_score", None),
    )

class GateIRAdapter:
    @staticmethod
    def from_gate(gate: object) -> CognitiveGateIR:
        total_severity, max_severity, instability_score = _extract_trace_metrics(gate)
        return CognitiveGateIR(
            verdict=_normalize_verdict(getattr(gate, "verdict", gate)),
            bundle_id=str(getattr(gate, "bundle_id", "")),
            reason_codes=_normalize_reason_codes(gate),
            risk_level=getattr(gate, "risk_level", None),
            triggered_rules=tuple(getattr(gate, "triggered_rules", ()) or ()),
            decision_trace=_map_trace(gate),
            total_severity=total_severity,
            max_severity=max_severity,
            instability_score=instability_score,
        )