# tests/kernel/stages/test_verdict_monotonic.py

"""Monotone verdict composition and provenance (audit F-001, lot A1+A2).

Covers the canonical strictness order, the enforce_monotone guard wired
around the enforcement gates, the provenance ledger, and the rewritten
global stability policy: confirm is a floor (hardens ALLOW), never a
ceiling, and the single sanctioned ABSTAIN -> REQUIRE_CONFIRMATION
reinterpretation requires a global-stability provenance.
"""

from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from arvis.kernel.pipeline.stages.gate.stability import (
    apply_global_stability_policy,
)
from arvis.kernel.pipeline.stages.gate.trace_helpers import (
    ASSESSMENT_PROVENANCE,
    GLOBAL_STABILITY_PROVENANCE,
    VERDICT_PROVENANCE_KEY,
    enforce_monotone,
    record_verdict_transition,
    seed_verdict_provenance,
    verdict_provenance,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.lyapunov.verdict_order import (
    is_relaxation,
    max_strictness,
    strictness,
)

VERDICTS = [
    LyapunovVerdict.ALLOW,
    LyapunovVerdict.REQUIRE_CONFIRMATION,
    LyapunovVerdict.ABSTAIN,
]


def _ctx(**kwargs):
    return SimpleNamespace(extra={}, **kwargs)


# ---------------------------------------------------------------
# Canonical order
# ---------------------------------------------------------------


def test_strictness_total_order():
    ranks = [strictness(v) for v in VERDICTS]
    assert ranks == sorted(ranks)
    assert len(set(ranks)) == len(VERDICTS)


@given(st.sampled_from(VERDICTS), st.sampled_from(VERDICTS))
def test_max_strictness_is_commutative_and_monotone(a, b):
    out = max_strictness(a, b)
    assert out == max_strictness(b, a)
    assert strictness(out) >= strictness(a)
    assert strictness(out) >= strictness(b)
    assert out in (a, b)


@given(st.sampled_from(VERDICTS), st.sampled_from(VERDICTS))
def test_is_relaxation_matches_order(before, after):
    assert is_relaxation(before, after) == (strictness(after) < strictness(before))


# ---------------------------------------------------------------
# enforce_monotone guard
# ---------------------------------------------------------------


@given(st.sampled_from(VERDICTS), st.sampled_from(VERDICTS))
def test_enforce_monotone_never_relaxes(before, after):
    ctx = _ctx()
    out = enforce_monotone(ctx, "some_gate", before, after)
    assert strictness(out) >= strictness(before)


def test_enforce_monotone_blocks_and_traces_relaxation():
    ctx = _ctx()
    out = enforce_monotone(
        ctx,
        "some_gate",
        LyapunovVerdict.ABSTAIN,
        LyapunovVerdict.ALLOW,
    )
    assert out is LyapunovVerdict.ABSTAIN
    trace = ctx.extra["verdict_transition_trace"]
    assert trace[-1]["stage"] == "some_gate_relaxation_blocked"
    assert trace[-1]["reason"] == "blocked_relaxation_to_ALLOW"


def test_enforce_monotone_passes_hardening_through():
    ctx = _ctx()
    out = enforce_monotone(
        ctx,
        "some_gate",
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.ABSTAIN,
    )
    assert out is LyapunovVerdict.ABSTAIN
    assert "verdict_transition_trace" not in ctx.extra


# ---------------------------------------------------------------
# Provenance ledger
# ---------------------------------------------------------------


def test_record_transition_records_provenance_on_hardening():
    ctx = _ctx()
    record_verdict_transition(
        ctx,
        stage="kappa_hard_block",
        before=LyapunovVerdict.ALLOW,
        after=LyapunovVerdict.ABSTAIN,
        reason="kappa_violation",
    )
    assert verdict_provenance(ctx, LyapunovVerdict.ABSTAIN) == "kappa_hard_block"


def test_record_transition_ignores_non_hardening():
    ctx = _ctx()
    record_verdict_transition(
        ctx,
        stage="whatever",
        before=LyapunovVerdict.ABSTAIN,
        after=LyapunovVerdict.ABSTAIN,
        reason="noop",
    )
    assert verdict_provenance(ctx, LyapunovVerdict.ABSTAIN) is None


def test_seed_attributes_global_stability_abstain():
    ctx = _ctx()
    ctx.extra["fusion_reasons"] = ["global_stability_enforced:abstain"]
    seed_verdict_provenance(ctx, LyapunovVerdict.ABSTAIN)
    assert (
        verdict_provenance(ctx, LyapunovVerdict.ABSTAIN) == GLOBAL_STABILITY_PROVENANCE
    )


def test_seed_attributes_assessment_by_default():
    ctx = _ctx()
    seed_verdict_provenance(ctx, LyapunovVerdict.ABSTAIN)
    assert verdict_provenance(ctx, LyapunovVerdict.ABSTAIN) == ASSESSMENT_PROVENANCE


def test_seed_never_overwrites_traced_provenance():
    ctx = _ctx()
    record_verdict_transition(
        ctx,
        stage="kappa_hard_block",
        before=LyapunovVerdict.ALLOW,
        after=LyapunovVerdict.ABSTAIN,
        reason="kappa_violation",
    )
    ctx.extra["fusion_reasons"] = ["global_stability_enforced:abstain"]
    seed_verdict_provenance(ctx, LyapunovVerdict.ABSTAIN)
    assert verdict_provenance(ctx, LyapunovVerdict.ABSTAIN) == "kappa_hard_block"


# ---------------------------------------------------------------
# Global stability policy (A2)
# ---------------------------------------------------------------


def test_confirm_hardens_allow_to_confirmation():
    ctx = _ctx(global_stability_action="confirm")
    out = apply_global_stability_policy(ctx, LyapunovVerdict.ALLOW, global_safe=False)
    assert out is LyapunovVerdict.REQUIRE_CONFIRMATION
    trace = ctx.extra["verdict_transition_trace"]
    assert trace[-1]["stage"] == "global_policy_confirm"


def test_confirm_keeps_confirmation():
    ctx = _ctx(global_stability_action="confirm")
    out = apply_global_stability_policy(
        ctx, LyapunovVerdict.REQUIRE_CONFIRMATION, global_safe=False
    )
    assert out is LyapunovVerdict.REQUIRE_CONFIRMATION


def test_confirm_never_relaxes_foreign_abstain():
    ctx = _ctx(global_stability_action="confirm")
    ctx.extra[VERDICT_PROVENANCE_KEY] = {"ABSTAIN": "kappa_hard_block"}
    out = apply_global_stability_policy(ctx, LyapunovVerdict.ABSTAIN, global_safe=False)
    assert out is LyapunovVerdict.ABSTAIN
    trace = ctx.extra["verdict_transition_trace"]
    assert trace[-1]["stage"] == "global_policy_confirm_denied"
    assert trace[-1]["reason"] == "abstain_provenance_not_global"


def test_confirm_fails_closed_on_unknown_provenance():
    ctx = _ctx(global_stability_action="confirm")
    out = apply_global_stability_policy(ctx, LyapunovVerdict.ABSTAIN, global_safe=False)
    assert out is LyapunovVerdict.ABSTAIN


def test_confirm_reinterprets_global_stability_abstain():
    ctx = _ctx(global_stability_action="confirm")
    ctx.extra[VERDICT_PROVENANCE_KEY] = {
        "ABSTAIN": GLOBAL_STABILITY_PROVENANCE,
    }
    out = apply_global_stability_policy(ctx, LyapunovVerdict.ABSTAIN, global_safe=False)
    assert out is LyapunovVerdict.REQUIRE_CONFIRMATION
    trace = ctx.extra["verdict_transition_trace"]
    assert trace[-1]["stage"] == "global_policy_confirm"


def test_confirm_kappa_flag_blocks_sanctioned_relaxation():
    ctx = _ctx(global_stability_action="confirm")
    ctx.extra[VERDICT_PROVENANCE_KEY] = {
        "ABSTAIN": GLOBAL_STABILITY_PROVENANCE,
    }
    ctx.extra["kappa_hard_block"] = True
    out = apply_global_stability_policy(ctx, LyapunovVerdict.ABSTAIN, global_safe=False)
    assert out is LyapunovVerdict.ABSTAIN


def test_abstain_action_hardens_and_traces():
    ctx = _ctx(global_stability_action="abstain")
    out = apply_global_stability_policy(ctx, LyapunovVerdict.ALLOW, global_safe=False)
    assert out is LyapunovVerdict.ABSTAIN
    assert "global_instability_abstain" in ctx.extra["fusion_reasons"]
    trace = ctx.extra["verdict_transition_trace"]
    assert trace[-1]["stage"] == "global_policy_abstain"


def test_ignore_action_leaves_verdict_untouched():
    ctx = _ctx(global_stability_action="ignore")
    for verdict in VERDICTS:
        out = apply_global_stability_policy(ctx, verdict, global_safe=False)
        assert out is verdict
    assert not any(
        "global_instability_" in r for r in ctx.extra.get("fusion_reasons", [])
    )


def test_global_safe_short_circuits():
    ctx = _ctx(global_stability_action="confirm")
    for verdict in VERDICTS:
        assert apply_global_stability_policy(ctx, verdict, global_safe=True) is verdict


@pytest.mark.parametrize("action", ["confirm", "abstain", "ignore"])
@given(
    verdict=st.sampled_from(VERDICTS),
    provenance=st.sampled_from(
        [None, ASSESSMENT_PROVENANCE, GLOBAL_STABILITY_PROVENANCE, "kappa_hard_block"]
    ),
    kappa_flag=st.booleans(),
)
def test_global_policy_monotone_except_sanctioned(
    action, verdict, provenance, kappa_flag
):
    """The only strictness decrease is the sanctioned, provenance-checked
    reinterpretation: ABSTAIN of global-stability provenance, action
    confirm, no kappa hard block. Everything else is monotone."""
    ctx = _ctx(global_stability_action=action)
    if provenance is not None:
        ctx.extra[VERDICT_PROVENANCE_KEY] = {"ABSTAIN": provenance}
    if kappa_flag:
        ctx.extra["kappa_hard_block"] = True

    out = apply_global_stability_policy(ctx, verdict, global_safe=False)

    sanctioned = (
        action == "confirm"
        and verdict is LyapunovVerdict.ABSTAIN
        and provenance == GLOBAL_STABILITY_PROVENANCE
        and not kappa_flag
    )
    if sanctioned:
        assert out is LyapunovVerdict.REQUIRE_CONFIRMATION
    else:
        assert strictness(out) >= strictness(verdict)
