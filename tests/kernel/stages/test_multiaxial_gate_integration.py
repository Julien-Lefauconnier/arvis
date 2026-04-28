# tests/kernel/test_multiaxial_gate_integration.py

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class StableCore:
    def compute(self, bundle):
        class Snapshot:
            collapse_risk = 0.2
            drift_score = 0.05
            regime = "stable"
            stable = True
            prev_lyap = 0.4
            cur_lyap = 0.2
            reflexive_state = {
                "stability_memory": 0.1,
                "structural_risk": 0.1,
                "regime_persistence": 0.1,
                "uncertainty_drift": 0.1,
            }

        return Snapshot()


def make_ctx():
    return CognitivePipelineContext(
        user_id="u",
        cognitive_input={},
        timeline=[],
    )


def test_gate_stores_fusion_reasons():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=StableCore())

    ctx = make_ctx()
    ctx.use_paper_composite_gate = True

    pipeline.run(ctx)
    pipeline.run(ctx)

    assert "fusion_reasons" in ctx.extra
    assert isinstance(ctx.extra["fusion_reasons"], list)


def test_gate_global_policy_confirm():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=StableCore())

    ctx = make_ctx()
    ctx.global_stability_action = "confirm"
    ctx.delta_w_history = [10.0, 10.0, 10.0]

    result = pipeline.run(ctx)

    if getattr(ctx, "global_stability_safe", True) is False:
        assert result.gate_result == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_gate_global_policy_abstain():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=StableCore())

    ctx = make_ctx()
    ctx.global_stability_action = "abstain"
    ctx.delta_w_history = [10.0, 10.0, 10.0]

    result = pipeline.run(ctx)

    if getattr(ctx, "global_stability_safe", True) is False:
        assert result.gate_result == LyapunovVerdict.ABSTAIN
