# tests/kernel/test_pipeline_contract.py

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext

from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal


class DummyCoreModel:
    def compute(self, bundle):
        class DummySnapshot:
            collapse_risk = 0.2
            drift_score = 0.1
            regime = "stable"
            stable = True
            prev_lyap = 0.5
            cur_lyap = 0.4

        return DummySnapshot()


def make_ctx():
    return CognitivePipelineContext(
        cognitive_input={},
        user_id="test_user",
        timeline=[],
    )


def test_pipeline_contract_outputs_signals():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=DummyCoreModel())

    ctx = make_ctx()
    pipeline.run(ctx)

    assert isinstance(ctx.collapse_risk, RiskSignal)
    assert isinstance(ctx.uncertainty, UncertaintySignal)
    assert isinstance(ctx.drift_score, DriftSignal)