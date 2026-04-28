# tests/kernel/test_stability_certificate.py


def test_pipeline_exposes_stability_certificate(pipeline, ctx):
    pipeline.run(ctx)

    assert hasattr(ctx, "stability_certificate")

    cert = ctx.stability_certificate

    assert isinstance(cert, dict)

    assert "local" in cert
    assert "global" in cert
    assert "switching" in cert


def test_stability_certificate_consistency(pipeline, ctx):
    pipeline.run(ctx)

    cert = ctx.stability_certificate

    # global flag must match context
    assert cert["global"] == getattr(ctx, "global_stability_safe")

    # switching flag must match context
    assert cert["switching"] == getattr(ctx, "switching_safe")
