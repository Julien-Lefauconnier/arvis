# tests/kernel/stages/tests_fusion_invariants_gate.py

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_gate_single_decision_point(pipeline, ctx):
    ctx.global_stability_action = "confirm"
    ctx.delta_w_history = [10.0, 10.0, 10.0]

    pipeline.run(ctx)

    # invariant fondamental
    assert "fusion_reasons" in ctx.extra
    assert isinstance(ctx.extra["fusion_reasons"], list)

    # cohérence verdict ↔ fusion
    if any("global_instability_confirm" in r for r in ctx.extra["fusion_reasons"]):
        assert ctx.gate_result == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_fusion_reason_consistency(pipeline, ctx):
    ctx.global_stability_action = "abstain"
    ctx.delta_w_history = [10.0, 10.0, 10.0]

    pipeline.run(ctx)

    reasons = ctx.extra["fusion_reasons"]

    # pas de contradictions
    assert not (
        any("confirm" in r for r in reasons) and any("abstain" in r for r in reasons)
    )


def test_fusion_trace_structure(pipeline, ctx):
    pipeline.run(ctx)

    trace = ctx.extra.get("fusion_trace")

    assert isinstance(trace, dict)
    assert "pre_verdict" in trace
    assert "final_verdict" in trace
    assert "reasons" in trace


def test_trace_matches_verdict(pipeline, ctx):
    ctx.global_stability_action = "abstain"
    ctx.delta_w_history = [10.0, 10.0, 10.0]

    pipeline.run(ctx)

    trace = ctx.extra["fusion_trace"]

    assert trace["final_verdict"] == str(ctx.gate_result)
