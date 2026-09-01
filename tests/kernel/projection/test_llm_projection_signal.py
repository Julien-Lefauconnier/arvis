# tests/kernel/projection/test_llm_projection_signal.py

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.projection.pi_impl import PiImpl


def test_llm_uncertainty_increases_projection():
    pi = PiImpl()

    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    ctx.extra = {
        "llm_observation": {
            "entropy_mean": 3.0,
            "logprob_variance": 1.0,
            "confidence_mean": 0.2,
        }
    }

    state = pi.project_structured(ctx)

    assert state.x.uncertainty_mass > 0.2
    assert state.w.ambiguity_pressure > state.x.uncertainty_mass
    assert state.z.gate.verdict in {"require_confirmation", "allow"}
