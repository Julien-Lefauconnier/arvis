# tests/kernel/stages/test_gate_stage_m8_trace.py


from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot


def _base_ctx():
    class Ctx:
        pass

    ctx = Ctx()
    ctx.prev_lyap = 1.0
    ctx.cur_lyap = 0.9
    ctx.delta_w_history = []
    ctx.extra = {}
    ctx.switching_runtime = None
    ctx.switching_params = None
    ctx.control_snapshot = None
    ctx.collapse_risk = 0.0
    ctx.stable = True
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

    ctx.prev_lyap = 1.0
    ctx.cur_lyap = 2.0  # strong increase → disturbance

    stage.run(pipeline, ctx)

    disturbance = ctx.extra["disturbance_signals"]
    val = disturbance["projection_disturbance"]

    assert val is not None
    assert val >= 0.0


def test_adaptive_warning_trigger():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    ctx.adaptive_snapshot = AdaptiveSnapshot(
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

    ctx.prev_lyap = 1.0

    # petites perturbations
    for i in range(10):
        ctx.cur_lyap = 1.0 + (0.01 * i)
        stage.run(pipeline, ctx)

        disturbance = ctx.extra["disturbance_signals"]["projection_disturbance"]
        assert disturbance is not None
        assert disturbance < 0.2  # borné


def test_slow_drift_detection():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    ctx.prev_lyap = 1.0

    triggered = False

    for i in range(50):
        ctx.cur_lyap = 1.0 + i * 0.001
        stage.run(pipeline, ctx)

        if ctx.extra.get("slow_drift_warning"):
            triggered = True

    assert triggered


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

    ctx.switching_runtime = FakeSwitch()
    ctx.switching_params = FakeParams()

    stage.run(pipeline, ctx)

    disturbance = ctx.extra["disturbance_signals"]
    assert disturbance["switching_disturbance"] is True



def test_recovery_after_instability():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    # phase instable
    ctx.prev_lyap = 1.0
    ctx.cur_lyap = 2.0
    stage.run(pipeline, ctx)

    assert ctx.gate_result != LyapunovVerdict.ALLOW

    # recovery
    ctx.prev_lyap = 2.0
    ctx.cur_lyap = 1.0
    stage.run(pipeline, ctx)

    assert ctx.gate_result in (
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
    )


def test_adaptive_instability_veto():
    stage = GateStage()
    ctx = _base_ctx()
    pipeline = _base_pipeline()

    ctx.adaptive_snapshot = AdaptiveSnapshot(
        kappa_eff=0.1,
        margin=0.01,
        regime="unstable",
        available=True,
    )

    stage.run(pipeline, ctx)

    assert ctx.gate_result == LyapunovVerdict.ABSTAIN


