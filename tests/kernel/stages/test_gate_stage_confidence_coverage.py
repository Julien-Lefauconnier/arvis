# tests/kernel/stages/test_gate_stage_confidence_coverage.py


from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot


class DummyCtx:
    def __init__(self):
        self.cur_lyap = 1.0
        self.prev_lyap = 1.0
        self.delta_w_history = []
        self.collapse_risk = 0.0
        self._cognitive_mode = CognitiveMode.NORMAL
        self._epsilon = 0.1

        self.switching_runtime = None
        self.switching_params = None

        self.stable = True

        self.extra = {}

        self.control_snapshot = CognitiveControlSnapshot(
            gate_mode="test",
            epsilon=0.1,
            smoothed_risk=0.0,
            lyap_verdict=None,
            exploration=0.5,
            drift=0.0,
            regime="test",
            calibration=None,
        )


def test_confidence_baseline():
    ctx = DummyCtx()
    GateStage().run(None, ctx)

    assert "system_confidence" in ctx.extra
    assert "confidence_flags" in ctx.extra
    assert isinstance(ctx.system_confidence, float)


def test_low_confidence_escalation():
    ctx = DummyCtx()
    ctx.collapse_risk = 1.0  # force mauvaise confiance

    GateStage().run(None, ctx)

    assert "confidence_flags" in ctx.extra
    if "very_low_confidence" in ctx.extra["confidence_flags"]:
        assert ctx.extra.get("low_confidence_escalation") is True


def test_no_control_snapshot_branch():
    ctx = DummyCtx()
    ctx.control_snapshot = None

    GateStage().run(None, ctx)

    assert "confidence_flags" in ctx.extra
    assert ctx.gate_result is not None


def test_fusion_fallback(monkeypatch):
    ctx = DummyCtx()

    def broken_fusion(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        broken_fusion,
    )

    GateStage().run(None, ctx)

    assert ctx.extra.get("fusion_error") is True
    assert "fusion_fallback" in ctx.extra.get("fusion_reasons", [])



def test_switching_warning():
    ctx = DummyCtx()

    class FakeRuntime:
        def dwell_time(self):
            return 0.0

    class FakeParams:
        J = 1.0
        eta = 1.0
        alpha = 1.0
        gamma_z = 1.0
        L_T = 1.0

    ctx.switching_runtime = FakeRuntime()
    ctx.switching_params = FakeParams()

    # force switching_condition = False
    import arvis.kernel.pipeline.stages.gate_stage as module

    def fake_switching(*args, **kwargs):
        return False

    module.switching_condition = fake_switching

    GateStage().run(None, ctx)

    assert ctx.extra.get("switching_warning") is True



def test_global_instability_flag(monkeypatch):
    ctx = DummyCtx()

    def fake_check(self, history):
        return False

    monkeypatch.setattr(
        "arvis.math.stability.global_guard.GlobalStabilityGuard.check",
        fake_check,
    )

    GateStage().run(None, ctx)

    assert ctx.extra.get("global_instability_warning") is True


def test_delta_positive_branch(monkeypatch):
    ctx = DummyCtx()

    def fake_delta(*args, **kwargs):
        return 1.0

    monkeypatch.setattr(
        "arvis.math.lyapunov.composite_lyapunov.CompositeLyapunov.delta_W",
        fake_delta,
    )

    GateStage().run(None, ctx)

    assert ctx.extra["composite_gate_recommendation"] is not None



