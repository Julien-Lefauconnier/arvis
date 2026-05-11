# # tests/kernel/test_pi_gate.py
from dataclasses import replace

from arvis.kernel.gate.pi_gate import PiBasedGate
from arvis.kernel.projection.pi_impl import PiImpl


def test_pi_gate_allow(minimal_ctx):
    pi = PiImpl().project_structured(minimal_ctx)
    gate = PiBasedGate()

    result = gate.evaluate(pi, bundle_id="b1")

    assert result.verdict.value == "allow"


def test_pi_gate_abstain(minimal_ctx):
    pi = PiImpl().project_structured(minimal_ctx)

    pi = replace(
        pi,
        x=replace(
            pi.x,
            conflict_pressure=0.95,
        ),
    )

    gate = PiBasedGate()

    result = gate.evaluate(pi, bundle_id="b1")

    assert result.verdict.value == "abstain"
    assert "high_instability_or_projection_failure" in result.reason_codes
    assert result.risk_level == 0.95


def test_pi_gate_confirmation(minimal_ctx):
    pi = PiImpl().project_structured(minimal_ctx)

    pi = replace(
        pi,
        w=replace(
            pi.w,
            uncertainty_pressure=0.75,
        ),
    )

    gate = PiBasedGate()

    result = gate.evaluate(pi, bundle_id="b1")

    assert result.verdict.value == "require_confirmation"
    assert "uncertainty_or_low_margin" in result.reason_codes
    assert result.risk_level == 0.75


def test_pi_gate_llm_risk_requires_confirmation(minimal_ctx):
    pi = PiImpl().project_structured(minimal_ctx)

    # Inject elevated LLM runtime risk
    pi = replace(
        pi,
        w=replace(
            pi.w,
            llm_risk_pressure=0.6,
        ),
    )

    gate = PiBasedGate()

    result = gate.evaluate(pi, bundle_id="b1")

    assert result.verdict.value == "require_confirmation"
    assert "elevated_llm_risk" in result.reason_codes
    assert result.risk_level == 0.6


def test_pi_gate_critical_llm_risk_abstains(minimal_ctx):
    pi = PiImpl().project_structured(minimal_ctx)

    # Inject critical LLM runtime risk
    pi = replace(
        pi,
        w=replace(
            pi.w,
            llm_risk_pressure=0.95,
        ),
    )

    gate = PiBasedGate()

    result = gate.evaluate(pi, bundle_id="b1")

    assert result.verdict.value == "abstain"
    assert "critical_llm_risk" in result.reason_codes
    assert result.risk_level == 0.95


def test_pi_gate_low_llm_risk_keeps_allow(minimal_ctx):
    pi = PiImpl().project_structured(minimal_ctx)

    pi = replace(
        pi,
        w=replace(
            pi.w,
            llm_risk_pressure=0.2,
        ),
    )

    gate = PiBasedGate()

    result = gate.evaluate(pi, bundle_id="b1")

    assert result.verdict.value == "allow"
    assert "critical_llm_risk" not in result.reason_codes
    assert "elevated_llm_risk" not in result.reason_codes
