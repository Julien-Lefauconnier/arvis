# tests/kernel/stages/test_gate_stage_coverage_boost.py

from types import SimpleNamespace

from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

# --------------------------------------------------
# Helpers
# --------------------------------------------------


def make_ctx():
    return SimpleNamespace(
        prev_lyap=1.0,
        cur_lyap=0.8,
        slow_state_prev=None,
        slow_state=None,
        symbolic_state_prev=None,
        symbolic_state=None,
        switching_runtime=None,
        switching_params=None,
        delta_w_history=[],
        extra={},
        stable=True,
    )


class DummyKernel:
    def __init__(self, verdict=LyapunovVerdict.ALLOW, recovery=False):
        self.pre_verdict = verdict
        self.final_verdict = verdict
        self.recovery_detected = recovery
        self.reasons = []
        self.certificate = {}


class DummyFusion:
    def __init__(self, verdict):
        self.verdict = verdict
        self.reasons = ["fusion_ok"]


# --------------------------------------------------
# 1. Basic run (happy path)
# --------------------------------------------------


def test_gate_stage_basic(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **kwargs: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **kwargs: kwargs["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result in {
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }
    assert "system_confidence" in ctx.extra


# --------------------------------------------------
# 2. Kernel recovery path
# --------------------------------------------------


def test_recovery_detected(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(recovery=True),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **kwargs: DummyFusion(LyapunovVerdict.ABSTAIN),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **kwargs: kwargs["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.extra.get("recovery_detected") is True


# --------------------------------------------------
# 3. Fusion fallback (exception)
# --------------------------------------------------


def test_fusion_exception(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )

    def crash(**kwargs):
        raise RuntimeError()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        crash,
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **kwargs: kwargs["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.extra.get("fusion_error") is True


# --------------------------------------------------
# 4. Adaptive unstable veto
# --------------------------------------------------


def test_adaptive_unstable(monkeypatch):
    ctx = make_ctx()

    ctx.adaptive_snapshot = SimpleNamespace(
        is_available=True,
        is_unstable=True,
        margin=0.2,
        kappa_eff=1.0,
        regime="test",
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **kwargs: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **kwargs: kwargs["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result == LyapunovVerdict.ABSTAIN


# --------------------------------------------------
# 5. Validity envelope violation
# --------------------------------------------------


def test_validity_envelope_block(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.build_validity_envelope",
        lambda **kwargs: SimpleNamespace(valid=False, reason="test"),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **kwargs: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **kwargs: kwargs["verdict"],
    )

    GateStage().run(None, ctx)

    assert "validity_test" in ctx.extra["fusion_reasons"]


# --------------------------------------------------
# 6. Kappa violation hard block
# --------------------------------------------------


def test_kappa_violation(monkeypatch):
    ctx = make_ctx()

    ctx.global_stability_metrics = SimpleNamespace(
        kappa_violation=True,
        kappa_gap=0.5,
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **kwargs: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **kwargs: kwargs["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result == LyapunovVerdict.ABSTAIN
    assert ctx.extra.get("kappa_hard_block") is True


# --------------------------------------------------
# 7. Composite recommendation path
# --------------------------------------------------


def test_composite_recommendation(monkeypatch):
    ctx = make_ctx()
    ctx.cur_lyap = 2.0
    ctx.prev_lyap = 1.0  # delta positive → decrease

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **kwargs: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **kwargs: kwargs["verdict"],
    )

    GateStage().run(None, ctx)

    assert "composite_gate_recommendation" in ctx.extra


# --------------------------------------------------
# 8. Observability paths
# --------------------------------------------------


def test_observability_payloads(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **kwargs: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **kwargs: kwargs["verdict"],
    )

    GateStage().run(None, ctx)

    assert "theoretical_trace" in ctx.extra
    assert "iss_perturbation" in ctx.extra
    assert "closed_loop_feedback" in ctx.extra


def test_gate_stage_composite_exception(monkeypatch):
    ctx = make_ctx()

    class BrokenComp:
        def W(self, *a, **k):
            raise RuntimeError()

        def delta_W(self, *a, **k):
            raise RuntimeError()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.CompositeLyapunov",
        lambda *a, **k: BrokenComp(),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    # On passe bien dans le except
    assert ctx.delta_w is not None


def test_switching_exception(monkeypatch):
    ctx = make_ctx()

    ctx.switching_runtime = object()
    ctx.switching_params = object()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.switching_condition",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError()),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.switching_safe is True


def test_global_guard_exception(monkeypatch):
    ctx = make_ctx()

    class BrokenGuard:
        def check(self, *_):
            raise RuntimeError()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.GlobalStabilityGuard",
        lambda: BrokenGuard(),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.global_stability_safe is True


def test_adaptive_fallback(monkeypatch):
    ctx = make_ctx()

    ctx.adaptive_snapshot = None  # fallback path

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.extra is not None


def test_validity_envelope_exception(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.build_validity_envelope",
        lambda **k: (_ for _ in ()).throw(RuntimeError()),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.validity_envelope is None


def test_no_observer_path(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert "confidence_flags" in ctx.extra


# --------------------------------------------------
# 9. Slow drift (full path)
# --------------------------------------------------


def test_gate_stage_full_slow_drift_detection(monkeypatch):
    ctx = make_ctx()

    ctx.slow_state_prev = 1.0
    ctx.slow_state = 1.001
    ctx.delta_w = 0.1  # positif

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert "slow_drift_warning" in ctx.extra


# --------------------------------------------------
# 10. Switching exception (duplicate path clean)
# --------------------------------------------------


def test_gate_stage_switching_exception_2(monkeypatch):
    ctx = make_ctx()

    ctx.switching_runtime = object()
    ctx.switching_params = object()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.switching_condition",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError()),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.switching_safe is True


# --------------------------------------------------
# 11. Fusion exception (explicit)
# --------------------------------------------------


def test_gate_stage_fusion_exception_2(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: (_ for _ in ()).throw(RuntimeError()),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.extra["fusion_error"] is True


# --------------------------------------------------
# 12. Validity enforcement (post-policy)
# --------------------------------------------------


def test_gate_stage_validity_enforcement(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.build_validity_envelope",
        lambda **k: SimpleNamespace(valid=False, reason="test"),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert "validity_test" in ctx.extra["fusion_reasons"]


# --------------------------------------------------
# 13. Kappa violation (final override)
# --------------------------------------------------


def test_gate_stage_kappa_violation_2(monkeypatch):
    ctx = make_ctx()

    class Metrics:
        kappa_violation = True
        kappa_gap = 0.5

    ctx.global_stability_metrics = Metrics()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.extra["kappa_hard_block"] is True
    assert ctx.gate_result == LyapunovVerdict.ABSTAIN


# --------------------------------------------------
# 14. Final adaptive unstable override
# --------------------------------------------------


def test_gate_stage_final_adaptive_unstable(monkeypatch):
    ctx = make_ctx()

    class FakeAdaptive:
        is_unstable = True
        is_available = True
        margin = 1.0
        kappa_eff = 1.0
        regime = "test"

    ctx.adaptive_snapshot = FakeAdaptive()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result == LyapunovVerdict.ABSTAIN


# --------------------------------------------------
# 15. Fusion trace update
# --------------------------------------------------


def test_gate_stage_fusion_trace_update(monkeypatch):
    ctx = make_ctx()

    ctx.extra["fusion_trace"] = {}

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert "final_verdict" in ctx.extra["fusion_trace"]


def test_gate_stage_full_exception_cascade(monkeypatch):
    ctx = make_ctx()

    class Boom:
        def __call__(self, *a, **k):
            raise RuntimeError()

    # Composite crash
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.CompositeLyapunov",
        lambda *a, **k: type(
            "X",
            (),
            {
                "W": Boom(),
                "delta_W": Boom(),
            },
        )(),
    )

    # Global guard crash
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.GlobalStabilityGuard",
        lambda: type("X", (), {"check": Boom()})(),
    )

    # Switching crash
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.switching_condition", Boom()
    )

    # Observer crash
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.GlobalStabilityObserver",
        lambda: type("X", (), {"update": Boom()})(),
    )

    # Kernel + fusion OK
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result is not None


def test_validity_forces_confirmation(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.build_validity_envelope",
        lambda **k: SimpleNamespace(valid=False, reason="forced"),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: LyapunovVerdict.ALLOW,
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_recovery_uncertain_forces_confirmation(monkeypatch):
    ctx = make_ctx()

    class K:
        pre_verdict = LyapunovVerdict.ABSTAIN
        final_verdict = LyapunovVerdict.ABSTAIN
        recovery_detected = True
        reasons = []
        certificate = {}

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel", lambda inputs: K()
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ABSTAIN),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.build_validity_envelope",
        lambda **k: SimpleNamespace(valid=False, reason="exponential_violation"),
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_recovery_valid_promotes_to_confirmation(monkeypatch):
    ctx = make_ctx()

    class K:
        pre_verdict = LyapunovVerdict.ABSTAIN
        final_verdict = LyapunovVerdict.ABSTAIN
        recovery_detected = True
        reasons = []
        certificate = {}

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel", lambda inputs: K()
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ABSTAIN),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.build_validity_envelope",
        lambda **k: SimpleNamespace(valid=True, reason=None),
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_trace_exception(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    # casse les attributs dynamiques
    ctx.projection_disturbance = "boom"

    GateStage().run(None, ctx)

    assert ctx.gate_result is not None


def test_adaptive_observer_creation(monkeypatch):
    ctx = make_ctx()

    class P:
        adaptive_kappa_estimator = object()

    pipeline = P()

    ctx.switching_runtime = type("X", (), {"dwell_time": lambda self: 1.0})()
    ctx.switching_params = type("X", (), {"J": 1})()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.AdaptiveRuntimeObserver",
        lambda **k: type("X", (), {"update": lambda *a, **k: None})(),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(pipeline, ctx)

    assert hasattr(pipeline, "adaptive_observer")


def test_recovery_exception_path(monkeypatch):
    ctx = make_ctx()

    ctx.prev_lyap = "boom"
    ctx.cur_lyap = object()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result is not None


def test_composite_recommendation_exception(monkeypatch):
    ctx = make_ctx()

    class BadPipeline:
        composite_rec_soft_threshold = "boom"

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(BadPipeline(), ctx)

    assert ctx.extra["composite_gate_recommendation"] is None


def test_fusion_exception_full(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: (_ for _ in ()).throw(RuntimeError()),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.extra["fusion_error"] is True


def test_validity_envelope_exception_real(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.build_validity_envelope",
        lambda **k: (_ for _ in ()).throw(RuntimeError()),
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.validity_envelope is None


def test_no_observer_branch(monkeypatch):
    ctx = make_ctx()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert "confidence_flags" in ctx.extra


def test_trace_and_iss_exception(monkeypatch):
    ctx = make_ctx()

    ctx.projection_disturbance = "boom"
    ctx.noise_disturbance = object()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result is not None


def test_gate_stage_bootstrap_defaults(monkeypatch):
    ctx = SimpleNamespace(
        prev_lyap=1.0,
        cur_lyap=0.8,
        stable=True,
    )

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert hasattr(ctx, "delta_w_history")
    assert hasattr(ctx, "extra")
    assert hasattr(ctx, "stability_certificate")
    assert hasattr(ctx, "system_confidence")


def test_gate_stage_creates_pipeline_observers(monkeypatch):
    ctx = SimpleNamespace(
        prev_lyap=1.0,
        cur_lyap=0.8,
        stable=True,
        extra={},
        delta_w_history=[],
        switching_runtime=type("R", (), {"dwell_time": lambda self: 1.0})(),
        switching_params=type(
            "P",
            (),
            {"J": 1.0, "eta": 0.1, "alpha": 0.1, "gamma_z": 1.0, "L_T": 1.0},
        )(),
    )

    class Pipeline:
        adaptive_kappa_estimator = object()

    pipeline = Pipeline()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.AdaptiveRuntimeObserver",
        lambda **k: type("Obs", (), {"update": lambda *a, **k: None})(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(pipeline, ctx)

    assert hasattr(pipeline, "adaptive_observer")
    assert hasattr(pipeline, "gate_observer")


class BadFloat:
    def __float__(self):
        raise RuntimeError()


def test_gate_stage_iss_exception_paths(monkeypatch):
    ctx = make_ctx()
    ctx.projection_disturbance = BadFloat()
    ctx.noise_disturbance = BadFloat()
    ctx.switching_disturbance = BadFloat()
    ctx.adversarial_disturbance = BadFloat()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result is not None


def test_gate_stage_validity_extended_exception(monkeypatch):
    ctx = make_ctx()
    ctx.validity_envelope = SimpleNamespace(valid=True, reason="ok")
    ctx.extra["validity_envelope"] = object()  # casse le **mapping unpack

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result is not None


def test_gate_stage_theoretical_trace_exception(monkeypatch):
    ctx = make_ctx()

    class BadMetrics:
        @property
        def kappa_eff(self):
            raise RuntimeError()

    ctx.global_stability_metrics = BadMetrics()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result is not None


def test_gate_stage_recovery_try_except(monkeypatch):
    ctx = make_ctx()
    ctx.prev_lyap = object()
    ctx.cur_lyap = object()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(None, ctx)

    assert ctx.gate_result is not None


def test_gate_stage_composite_rec_try_except(monkeypatch):
    ctx = make_ctx()

    class BadPipeline:
        composite_rec_soft_threshold = object()
        composite_rec_strong_threshold = object()

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_gate_kernel",
        lambda inputs: DummyKernel(),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: DummyFusion(LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.apply_gate_policy",
        lambda **k: k["verdict"],
    )

    GateStage().run(BadPipeline(), ctx)

    assert ctx.extra["composite_gate_recommendation"] is None
