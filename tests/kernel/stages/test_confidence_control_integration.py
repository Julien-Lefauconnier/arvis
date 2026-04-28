# tests/kernel/gate/test_confidence_control_integration.py


def test_confidence_flags_present(pipeline, ctx):
    ctx.delta_w_history = [10.0, 10.0, 10.0]

    pipeline.run(ctx)

    assert "confidence_flags" in ctx.extra


def test_low_confidence_escalation_flag(pipeline, ctx):
    ctx.delta_w_history = [10.0, 10.0, 10.0]

    pipeline.run(ctx)

    flags = ctx.extra.get("confidence_flags", [])

    if "very_low_confidence" in flags:
        assert ctx.extra.get("low_confidence_escalation") is True


def test_control_snapshot_modified(pipeline, ctx):
    pipeline.run(ctx)

    snap = ctx.control_snapshot

    assert snap.epsilon is not None
    assert snap.exploration is not None
