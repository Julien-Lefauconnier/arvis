# tests/kernel/test_global_stability_integration.py

def test_pipeline_tracks_global_stability(pipeline, ctx):
    # run multiple steps to build history
    for _ in range(5):
        pipeline.run(ctx)

    assert hasattr(ctx, "delta_w_history")
    assert isinstance(ctx.delta_w_history, list)
    assert hasattr(ctx, "global_stability_safe")