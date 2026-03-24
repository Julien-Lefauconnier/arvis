# tests/adapters/ir/test_gate_adapter.py

from __future__ import annotations

from enum import Enum
from types import SimpleNamespace

from arvis.adapters.ir.gate_adapter import GateIRAdapter
from arvis.ir.gate import CognitiveGateVerdictIR


class DummyVerdict(str, Enum):
    ALLOW = "allow"
    ABSTAIN = "abstain"


def test_gate_adapter_maps_reason_string_to_codes() -> None:
    gate = SimpleNamespace(
        verdict=DummyVerdict.ALLOW,
        reason="high_cognitive_risk|memory_write_requires_confirmation",
        bundle_id="bundle-1",
    )

    ir = GateIRAdapter.from_gate(gate)

    assert ir.verdict == CognitiveGateVerdictIR.ALLOW
    assert ir.bundle_id == "bundle-1"
    assert ir.reason_codes == (
        "high_cognitive_risk",
        "memory_write_requires_confirmation",
    )


def test_gate_adapter_accepts_explicit_reason_codes() -> None:
    gate = SimpleNamespace(
        verdict="LyapunovVerdict.ABSTAIN",
        reason_codes=("cognitive_instability_detected",),
        bundle_id="bundle-2",
        triggered_rules=("global_guard",),
        risk_level=0.91,
    )

    ir = GateIRAdapter.from_gate(gate)

    assert ir.verdict == CognitiveGateVerdictIR.ABSTAIN
    assert ir.reason_codes == ("cognitive_instability_detected",)
    assert ir.triggered_rules == ("global_guard",)
    assert ir.risk_level == 0.91