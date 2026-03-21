# tests/kernel/test_system_confidence_integration.py

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext


class DummyCoreModel:
    def compute(self, bundle):
        class Snapshot:
            collapse_risk = 0.2
            drift_score = 0.1
            regime = "stable"
            stable = True
            cur_lyap = 0.4
            reflexive_state = {
                "stability_memory": 0.1,
                "structural_risk": 0.1,
                "regime_persistence": 0.1,
                "uncertainty_drift": 0.1,
            }

        return Snapshot()


def make_ctx() -> CognitivePipelineContext:
    return CognitivePipelineContext(
        user_id="test-user",
        cognitive_input={"query": "test"},
        timeline=[],
    )


def test_pipeline_exposes_system_confidence():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    pipeline.run(ctx)

    assert hasattr(ctx, "system_confidence")
    assert isinstance(ctx.system_confidence, float)
    assert 0.0 <= ctx.system_confidence <= 1.0


def test_fusion_trace_contains_system_confidence():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    pipeline.run(ctx)

    trace = ctx.extra.get("fusion_trace")

    assert isinstance(trace, dict)
    assert "system_confidence" in trace
    assert 0.0 <= float(trace["system_confidence"]) <= 1.0


def test_extra_contains_system_confidence():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    pipeline.run(ctx)

    assert "system_confidence" in ctx.extra
    assert 0.0 <= float(ctx.extra["system_confidence"]) <= 1.0