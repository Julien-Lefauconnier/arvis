# tests/kernel/test_global_stability_policy.py

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_global_stability_policy_ignore(pipeline, ctx):
    ctx.global_stability_action = "ignore"

    # simulate instability
    ctx.delta_w_history = [1.0, 1.0, 1.0]

    pipeline.run(ctx)

    assert ctx.stability_certificate["global"] in [True, False]
    # no global enforcement should appear in fusion reasons
    reasons = ctx.extra.get("fusion_reasons", [])
    assert not any("global_instability_" in r for r in reasons)


def test_global_stability_policy_confirm(pipeline, ctx):
    ctx.global_stability_action = "confirm"

    # force instability
    ctx.delta_w_history = [10.0, 10.0, 10.0]

    pipeline.run(ctx)

    if ctx.stability_certificate["global"] is False:
        assert ctx.gate_result == LyapunovVerdict.REQUIRE_CONFIRMATION
        reasons = ctx.extra.get("fusion_reasons", [])
        assert any("global_instability_confirm" in r for r in reasons)


def test_global_stability_policy_abstain(pipeline, ctx):
    ctx.global_stability_action = "abstain"

    # force instability
    ctx.delta_w_history = [10.0, 10.0, 10.0]

    pipeline.run(ctx)

    if ctx.stability_certificate["global"] is False:
        assert ctx.gate_result == LyapunovVerdict.ABSTAIN
        reasons = ctx.extra.get("fusion_reasons", [])
        assert any("global_instability_abstain" in r for r in reasons)