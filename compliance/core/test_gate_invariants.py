# compliance/core/test_gate_invariants.py

from arvis.ir.gate import CognitiveGateVerdictIR
from compliance.helpers import run_ctx
from compliance.scenarios.builders import (
    build_kappa_violation_context,
    build_projection_invalid_context,
    build_validity_invalid_context,
)


def test_projection_invalid_forces_abstain():
    ctx = build_projection_invalid_context()
    result = run_ctx(ctx)

    assert result.ir_gate.verdict != CognitiveGateVerdictIR.ALLOW


def test_validity_invalid_forces_abstain():
    ctx = build_validity_invalid_context()
    result = run_ctx(ctx)

    assert result.ir_gate.verdict == CognitiveGateVerdictIR.ABSTAIN


def test_kappa_violation_blocks_allow():
    ctx = build_kappa_violation_context()
    result = run_ctx(ctx)

    assert result.ir_gate.verdict != CognitiveGateVerdictIR.ALLOW


def test_validity_false_implies_abstain():
    ctx = build_validity_invalid_context()
    result = run_ctx(ctx)

    assert result.ir_validity["valid"] is False
    assert result.ir_gate.verdict == CognitiveGateVerdictIR.ABSTAIN
