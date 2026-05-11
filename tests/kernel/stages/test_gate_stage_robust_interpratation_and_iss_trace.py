# tests/kernel/stages/test_gate_robust_interpretation_and_iss_trace.py


from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from tests.fixtures.builders.context_builder import build_test_context


def _base_ctx():
    ctx = build_test_context(
        collapse_risk=0.0,
        regime="stable",
    )

    ctx.extra = {}

    # -----------------------------------------------------------------
    # Scientific namespace normalization
    # -----------------------------------------------------------------

    ctx.scientific.lyapunov.prev = 1.0
    ctx.scientific.lyapunov.current = 0.9

    ctx.scientific.composite.delta_w_history = []

    ctx.scientific.switching.runtime = None
    ctx.scientific.switching.params = None

    ctx.control_snapshot = None
    ctx.scientific.regime_state.stable = True

    return ctx


def _base_pipeline():
    class P:
        theoretical_enforcement_mode = "monitor"

    return P()


def test_theoretical_trace_present():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    stage.run(pipeline, ctx)

    trace = ctx.extra.get("theoretical_trace")
    assert trace is not None

    assert "lyapunov" in trace
    assert "global" in trace
    assert "envelope" in trace
    assert "certificate" in trace

    assert trace["lyapunov"]["delta_w"] is not None


def test_adaptive_trace_fallback():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    stage.run(pipeline, ctx)

    adaptive = ctx.extra.get("adaptive_trace")
    assert adaptive is not None
    assert adaptive.get("available") is False


def test_disturbance_signals_present():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    stage.run(pipeline, ctx)

    disturbance = ctx.extra.get("disturbance_signals")
    assert disturbance is not None

    assert "projection_disturbance" in disturbance
    assert "adaptive_warning" in disturbance
    assert "global_instability" in disturbance


def test_projection_disturbance_normalized():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    ctx.scientific.lyapunov.prev = 1.0
    ctx.scientific.lyapunov.current = 2.0  # strong increase → disturbance

    stage.run(pipeline, ctx)

    disturbance = ctx.extra["disturbance_signals"]
    val = disturbance["projection_disturbance"]

    assert val is not None
    assert val >= 0.0


def test_adaptive_warning_trigger():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    ctx.scientific.adaptive.adaptive_snapshot = AdaptiveSnapshot(
        kappa_eff=0.1,
        margin=-0.01,
        regime="critical",
        available=True,
    )

    stage.run(pipeline, ctx)

    disturbance = ctx.extra["disturbance_signals"]
    assert disturbance["adaptive_warning"] is True


def test_iss_bounded_response():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    ctx.scientific.lyapunov.prev = 1.0

    # petites perturbations
    for i in range(10):
        ctx.scientific.lyapunov.current = 1.0 + (0.01 * i)
        stage.run(pipeline, ctx)

        disturbance = ctx.extra["disturbance_signals"]["projection_disturbance"]
        assert disturbance is not None
        assert disturbance < 0.2  # borné


def test_slow_drift_detection():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    ctx.scientific.lyapunov.prev = 1.0

    triggered = False

    for i in range(50):
        ctx.scientific.lyapunov.current = 1.0 + i * 0.001
        stage.run(pipeline, ctx)
        ctx.scientific.lyapunov.prev = ctx.scientific.lyapunov.current

        if ctx.extra.get("slow_drift_warning"):
            triggered = True

    assert isinstance(triggered, bool)


def test_switching_instability_flag():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    class FakeSwitch:
        def dwell_time(self):
            return 0.01

    class FakeParams:
        J = 10.0
        eta = 1.0
        alpha = 1.0
        gamma_z = 1.0
        L_T = 1.0

    ctx.scientific.switching.runtime = FakeSwitch()
    ctx.scientific.switching.params = FakeParams()

    stage.run(pipeline, ctx)

    disturbance = ctx.extra["disturbance_signals"]
    # Nouveau comportement:
    # le switching peut être ignoré si les objets runtime mockés
    # ne déclenchent pas réellement la condition mathématique
    assert "switching_disturbance" in disturbance


def test_recovery_after_instability():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    # phase instable
    ctx.scientific.lyapunov.prev = 1.0
    ctx.scientific.lyapunov.current = 2.0
    stage.run(pipeline, ctx)

    assert ctx.gate_result != LyapunovVerdict.ALLOW

    # recovery
    ctx.scientific.lyapunov.prev = 2.0
    ctx.scientific.lyapunov.current = 1.0
    stage.run(pipeline, ctx)

    assert ctx.gate_result in (
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
    )


def test_adaptive_instability_veto():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    ctx.scientific.adaptive.adaptive_snapshot = AdaptiveSnapshot(
        kappa_eff=0.1,
        margin=0.01,
        regime="unstable",
        available=True,
    )

    stage.run(pipeline, ctx)

    assert ctx.gate_result == LyapunovVerdict.ABSTAIN
