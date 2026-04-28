# # tests/kernel/test_pi_gate.py

from arvis.kernel.gate.pi_gate import PiBasedGate
from arvis.kernel.projection.pi_impl import PiImpl


def test_pi_gate_allow(minimal_ctx):
    pi = PiImpl().project_structured(minimal_ctx)
    gate = PiBasedGate()

    result = gate.evaluate(pi, bundle_id="b1")

    assert result.verdict.value == "allow"


def test_pi_gate_abstain(minimal_ctx):
    minimal_ctx.drift_score = 0.95  # instability

    pi = PiImpl().project_structured(minimal_ctx)
    gate = PiBasedGate()

    result = gate.evaluate(pi, bundle_id="b1")

    assert result.verdict.value == "abstain"


def test_pi_gate_confirmation(minimal_ctx):
    minimal_ctx.uncertainty = 0.9

    pi = PiImpl().project_structured(minimal_ctx)
    gate = PiBasedGate()

    result = gate.evaluate(pi, bundle_id="b1")

    assert result.verdict.value == "require_confirmation"
