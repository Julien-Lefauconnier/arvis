# tests/kernel/test_pi_structured.py

import pytest

from arvis.kernel.projection.pi_impl import PiImpl
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext

from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR
from arvis.ir.state import CognitiveStateIR, CognitiveRiskIR


# ============================================================
# 🔧 FIXTURE : minimal realistic pipeline context
# ============================================================

@pytest.fixture
def minimal_ctx():
    return CognitivePipelineContext(
        user_id="test_user",
        cognitive_input=None,
        system_tension=0.4,
        drift_score=0.1,
        uncertainty=0.2,
        collapse_risk=0.3,
        regime="stable",
        switching_safe=True,
        delta_w=0.05,
    )


@pytest.fixture
def ctx_with_ir(minimal_ctx):
    minimal_ctx.ir_decision = CognitiveDecisionIR(
        decision_id="d1",
        decision_kind="action",
        memory_intent="none",
    )

    minimal_ctx.ir_gate = CognitiveGateIR(
        verdict=CognitiveGateVerdictIR.ALLOW,
        bundle_id="b1",
        reason_codes=("ok",),
        risk_level=0.2,
    )

    minimal_ctx.ir_state = CognitiveStateIR(
        state_id="s1",
        bundle_id="b1",
        dv=0.1,
        collapse_risk=CognitiveRiskIR(
            mh_risk=0.1,
            world_risk=0.2,
            forecast_risk=0.3,
            fused_risk=0.3,
            smoothed_risk=0.25,
        ),
        epsilon=0.15,
        early_warning=False,
    )

    return minimal_ctx


# ============================================================
# ✅ TEST 1 : Determinism (critical)
# ============================================================

def test_pi_structured_deterministic(ctx_with_ir):
    pi = PiImpl()

    s1 = pi.project_structured(ctx_with_ir)
    s2 = pi.project_structured(ctx_with_ir)

    assert s1 == s2


# ============================================================
# ✅ TEST 2 : Structure integrity
# ============================================================

def test_pi_structured_has_all_components(ctx_with_ir):
    pi = PiImpl()
    s = pi.project_structured(ctx_with_ir)

    assert s.x is not None
    assert s.z is not None
    assert s.q is not None
    assert s.w is not None


# ============================================================
# ✅ TEST 3 : Value ranges (stability sanity)
# ============================================================

def test_pi_value_ranges(ctx_with_ir):
    pi = PiImpl()
    s = pi.project_structured(ctx_with_ir)

    assert 0.0 <= s.x.coherence_score <= 1.0
    assert 0.0 <= s.x.symbolic_stability <= 1.0

    assert 0.0 <= s.z.decision.confidence_score <= 1.0
    assert 0.0 <= s.z.control.epsilon <= 1.0

    assert s.z.gate.verdict in ["allow", "require_confirmation", "abstain"]


# ============================================================
# ✅ TEST 4 : Gate coherence
# ============================================================

def test_gate_consistency(ctx_with_ir):
    pi = PiImpl()
    s = pi.project_structured(ctx_with_ir)

    verdict = ctx_with_ir.ir_gate.verdict.value

    assert s.z.gate.verdict == verdict

    if verdict == "require_confirmation":
        assert s.z.gate.confirmation_required is True
    else:
        assert s.z.gate.confirmation_required is False


# ============================================================
# ✅ TEST 5 : Sensitivity to uncertainty
# ============================================================

def test_uncertainty_impacts_confidence(minimal_ctx):
    pi = PiImpl()

    minimal_ctx.uncertainty = 0.1
    s_low = pi.project_structured(minimal_ctx)

    minimal_ctx.uncertainty = 0.9
    s_high = pi.project_structured(minimal_ctx)

    assert s_low.z.decision.confidence_score > s_high.z.decision.confidence_score


# ============================================================
# ✅ TEST 6 : Stability signal propagation
# ============================================================

def test_system_tension_propagation(minimal_ctx):
    pi = PiImpl()

    minimal_ctx.system_tension = 0.2
    s1 = pi.project_structured(minimal_ctx)

    minimal_ctx.system_tension = 0.8
    s2 = pi.project_structured(minimal_ctx)

    assert s2.x.cognitive_load > s1.x.cognitive_load
    assert s2.z.dynamics.temporal_pressure > s1.z.dynamics.temporal_pressure


# ============================================================
# ✅ TEST 7 : Drift affects stability
# ============================================================

def test_drift_affects_symbolic_stability(minimal_ctx):
    pi = PiImpl()

    minimal_ctx.drift_score = 0.1
    s_low = pi.project_structured(minimal_ctx)

    minimal_ctx.drift_score = 0.9
    s_high = pi.project_structured(minimal_ctx)

    assert s_low.x.symbolic_stability > s_high.x.symbolic_stability


# ============================================================
# ✅ TEST 8 : Projection residual logic
# ============================================================

def test_projection_residual_behavior(ctx_with_ir):
    pi = PiImpl()

    ctx_with_ir.projection_margin = 0.9
    s_high_margin = pi.project_structured(ctx_with_ir)

    ctx_with_ir.projection_margin = 0.1
    s_low_margin = pi.project_structured(ctx_with_ir)

    assert s_high_margin.w.projection_residual < s_low_margin.w.projection_residual


# ============================================================
# ✅ TEST 9 : Switching safety propagation
# ============================================================

def test_switching_flag_propagation(minimal_ctx):
    pi = PiImpl()

    minimal_ctx.switching_safe = True
    s_safe = pi.project_structured(minimal_ctx)

    minimal_ctx.switching_safe = False
    s_unsafe = pi.project_structured(minimal_ctx)

    assert s_safe.q.switching_safe is True
    assert s_unsafe.q.switching_safe is False


# ============================================================
# ✅ TEST 10 : Robustness to missing IR
# ============================================================

def test_no_ir_does_not_crash(minimal_ctx):
    pi = PiImpl()

    minimal_ctx.ir_decision = None
    minimal_ctx.ir_gate = None
    minimal_ctx.ir_state = None

    s = pi.project_structured(minimal_ctx)

    assert s is not None
    assert s.z.gate.verdict in ["allow", "require_confirmation", "abstain"]