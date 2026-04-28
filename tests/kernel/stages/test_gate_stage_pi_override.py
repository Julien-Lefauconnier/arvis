# tests/kernel/stages/test_gate_stage_pi_override.py

from unittest.mock import patch

from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


# ============================================================
# Dummy context minimal compatible GateStage
# ============================================================


class DummyCtx:
    def __init__(self):
        self.extra = {}
        self.prev_lyap = 0.5
        self.cur_lyap = 0.4
        self.delta_w = -0.1
        self.w_prev = 0.5
        self.w_current = 0.4

        self.stable = True

        self.switching_runtime = None
        self.switching_params = None

        self.symbolic_state = None
        self.symbolic_state_prev = None
        self.slow_state = None
        self.slow_state_prev = None

        self.collapse_risk = 0.0

        self.projection_certificate = None
        self.projection_view = None
        self.projected_state = None

        self.pi_state = object()

        self.gate_result = None


class DummyPipeline:
    pass


# ============================================================
# Helpers
# ============================================================


class DummyPiResult:
    def __init__(self, verdict, risk="low"):
        self.verdict = type("V", (), {"value": verdict})()
        self.risk_level = risk


# ============================================================
# TESTS
# ============================================================


def test_pi_can_downgrade_allow_to_confirmation():
    ctx = DummyCtx()
    pipeline = DummyPipeline()
    stage = GateStage()

    with patch(
        "arvis.kernel.pipeline.stages.gate_stage.PiBasedGate.evaluate",
        return_value=DummyPiResult("require_confirmation"),
    ):
        stage.run(pipeline, ctx)

    assert ctx.gate_result in {
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }
    assert ctx.extra["pi_gate_verdict"] == "require_confirmation"


def test_pi_can_force_abstain():
    ctx = DummyCtx()
    pipeline = DummyPipeline()
    stage = GateStage()

    with patch(
        "arvis.kernel.pipeline.stages.gate_stage.PiBasedGate.evaluate",
        return_value=DummyPiResult("abstain"),
    ):
        stage.run(pipeline, ctx)

    assert ctx.gate_result == LyapunovVerdict.ABSTAIN
    assert ctx.extra["pi_gate_verdict"] == "abstain"


def test_pi_cannot_relax_abstain():
    ctx = DummyCtx()
    pipeline = DummyPipeline()
    stage = GateStage()

    with patch(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
    ) as mock_fusion:

        class DummyFusionResult:
            verdict = LyapunovVerdict.ABSTAIN
            reasons = []

        mock_fusion.return_value = DummyFusionResult()

        with patch(
            "arvis.kernel.pipeline.stages.gate_stage.PiBasedGate.evaluate",
            return_value=DummyPiResult("allow"),
        ):
            stage.run(pipeline, ctx)

    assert ctx.gate_result in {
        LyapunovVerdict.ABSTAIN,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
    }


def test_pi_ignored_if_no_pi_state():
    ctx = DummyCtx()
    ctx.pi_state = None  # désactivation Π
    pipeline = DummyPipeline()
    stage = GateStage()

    with patch(
        "arvis.kernel.pipeline.stages.gate_stage.PiBasedGate.evaluate",
        return_value=DummyPiResult("abstain"),
    ):
        stage.run(pipeline, ctx)

    # aucune trace Π
    assert "pi_gate_verdict" not in ctx.extra


def test_pi_observability_fields_present():
    ctx = DummyCtx()
    pipeline = DummyPipeline()
    stage = GateStage()

    with patch(
        "arvis.kernel.pipeline.stages.gate_stage.PiBasedGate.evaluate",
        return_value=DummyPiResult("require_confirmation", risk="medium"),
    ):
        stage.run(pipeline, ctx)

    assert ctx.extra["pi_gate_verdict"] == "require_confirmation"
    assert ctx.extra["pi_gate_risk"] == "medium"


def test_pi_override_trace_recorded():
    ctx = DummyCtx()
    pipeline = DummyPipeline()
    stage = GateStage()

    with patch(
        "arvis.kernel.pipeline.stages.gate_stage.PiBasedGate.evaluate",
        return_value=DummyPiResult("abstain"),
    ):
        stage.run(pipeline, ctx)

    trace = ctx.extra.get("verdict_transition_trace", [])
    assert any(t["stage"] == "pi_gate_override" for t in trace)


def test_pi_failure_is_safe():
    ctx = DummyCtx()
    pipeline = DummyPipeline()
    stage = GateStage()

    with patch(
        "arvis.kernel.pipeline.stages.gate_stage.PiBasedGate.evaluate",
        side_effect=Exception("boom"),
    ):
        stage.run(pipeline, ctx)

    assert "pi_gate_failure" in ctx.extra.get("errors", [])
    assert ctx.gate_result is not None  # pipeline continue
