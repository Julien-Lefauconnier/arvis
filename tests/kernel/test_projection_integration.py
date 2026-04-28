# tests/kernel/pipeline/test_projection_integration.py


def test_projection_integration_basic():
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )

    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="test",
        cognitive_input={"text": "hello"},
    )

    pipeline.run(ctx)

    assert ctx.projection_certificate is not None
    assert ctx.projection_domain_valid is not None
    assert ctx.projection_certificate.domain_valid is not None
