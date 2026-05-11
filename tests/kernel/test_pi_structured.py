# tests/kernel/test_pi_structured.py

from arvis.kernel.projection.pi_impl import PiImpl

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


# ============================================================
# ✅ TEST 6 : Stability signal propagation
# ============================================================


# ============================================================
# ✅ TEST 7 : Drift affects stability
# ============================================================


# ============================================================
# ✅ TEST 8 : Projection residual logic
# ============================================================


def test_projection_residual_behavior(ctx_with_ir):
    pi = PiImpl()

    ctx_with_ir.projection.margin = 0.9
    s_high_margin = pi.project_structured(ctx_with_ir)

    ctx_with_ir.projection.margin = 0.1
    s_low_margin = pi.project_structured(ctx_with_ir)

    assert s_high_margin.w.projection_residual < s_low_margin.w.projection_residual


# ============================================================
# ✅ TEST 9 : Switching safety propagation
# ============================================================


def test_switching_flag_propagation(minimal_ctx):
    pi = PiImpl()

    minimal_ctx.scientific.switching.switching_safe = True
    s_safe = pi.project_structured(minimal_ctx)

    minimal_ctx.scientific.switching.switching_safe = False
    s_unsafe = pi.project_structured(minimal_ctx)

    assert s_safe.q.switching_safe is True
    assert s_unsafe.q.switching_safe is False


# ============================================================
# ✅ TEST 10 : Robustness to missing IR
# ============================================================


def test_no_ir_does_not_crash(minimal_ctx):
    pi = PiImpl()

    minimal_ctx.decision_layer.ir_decision = None
    minimal_ctx.ir_gate = None
    minimal_ctx.ir_state = None

    s = pi.project_structured(minimal_ctx)

    assert s is not None
    assert s.z.gate.verdict in ["allow", "require_confirmation", "abstain"]
