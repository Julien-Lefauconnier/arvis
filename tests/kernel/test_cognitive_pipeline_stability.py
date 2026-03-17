# tests/kernel/test_cognitive_pipeline_stability.py

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext


class IncreasingRiskCore:
    def compute(self, bundle):
        class Dummy:
            collapse_risk = 0.8
            drift_score = 0.9
            regime = "unstable"
            stable = False
            prev_lyap = 0.2
            cur_lyap = 1.2
        return Dummy()


def test_high_risk_leads_to_block():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=IncreasingRiskCore())

    ctx = CognitivePipelineContext(
     cognitive_input={},
     user_id="u",
     timeline=[],
 )

    result = pipeline.run(ctx)

    assert result.executable_intent is None