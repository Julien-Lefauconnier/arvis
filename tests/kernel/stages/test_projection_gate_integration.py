# tests/kernel/stages/test_projection_gate_integration.py


def test_projection_invalid_blocks_allow():
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )

    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="test",
        cognitive_input={"text": "hello"},
    )

    # Force invalid projection
    ctx.projection_domain_valid = False

    result = pipeline.run(ctx)

    assert result.gate_result is not None
