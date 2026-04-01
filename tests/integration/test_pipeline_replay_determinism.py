# tests/integration/test_pipeline_replay_determinism.py

def test_pipeline_replay_determinism():
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
    from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext

    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="user-1",
        cognitive_input={"input_id": "test"},
    )

    # run normal
    result_1 = pipeline.run(ctx)

    assert result_1.cognitive_ir is not None
    assert result_1.ir_hash is not None

    # replay from IR
    result_2 = pipeline.run_from_ir(result_1.cognitive_ir)

    assert result_2.ir_hash == result_1.ir_hash