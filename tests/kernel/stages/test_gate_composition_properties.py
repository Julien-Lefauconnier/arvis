# tests/kernel/stages/test_gate_composition_properties.py

"""Composition-level guarantees of the gate stack (lots A3 to A6).

A3: fail-closed composition. A failing fusion abstains instead of
falling back to the pre-fusion verdict, and an unavailable validity
envelope (build failure) abstains instead of silently not gating.
A4: switching safety envelope mode: soft by default (observability
only), enforced under any other value (unknown modes fail closed).
A5: versioned severity table behind the envelope hard_block flag.
A6: pipeline-level property: the verdict transition trace never
contains a relaxation outside the sanctioned, documented channels.
"""

from types import SimpleNamespace

from hypothesis import given, settings
from hypothesis import strategies as st

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel.pipeline.stages.gate.decision_stack import run_gate_fusion
from arvis.kernel.pipeline.stages.gate.stability import build_validity_envelope
from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.lyapunov.verdict_order import VERDICT_STRICTNESS
from arvis.math.stability.hard_block_policy import (
    DEFAULT_SEVERITY_TABLE,
    HARD_BLOCK_TABLE_VERSION,
    StabilitySeverity,
    resolve_hard_block,
)

# ---------------------------------------------------------------
# A3: fusion failure fails closed
# ---------------------------------------------------------------


def test_fusion_failure_fails_closed(monkeypatch):
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.run_fusion",
        lambda **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    ctx = SimpleNamespace(extra={})
    kernel_result = SimpleNamespace(final_verdict=LyapunovVerdict.ALLOW)

    out = run_gate_fusion(
        ctx=ctx,
        pre_verdict=LyapunovVerdict.ALLOW,
        kernel_result=kernel_result,
        delta_w=None,
        switching_safe=True,
        global_safe=True,
        adaptive_metrics=None,
    )

    assert out is LyapunovVerdict.ABSTAIN
    assert ctx.extra["fusion_error"] is True
    assert "fusion_fallback" in ctx.extra["fusion_reasons"]
    trace = ctx.extra["verdict_transition_trace"]
    assert trace[-1]["stage"] == "fusion_fail_closed"
    assert trace[-1]["reason"] == "gate_exception"


# ---------------------------------------------------------------
# A3: unavailable validity envelope fails closed
# ---------------------------------------------------------------


def _stage_ctx() -> SimpleNamespace:
    return SimpleNamespace(
        prev_lyap=1.0,
        cur_lyap=0.9,
        delta_w_history=[],
        extra={},
        switching_runtime=None,
        switching_params=None,
        control_snapshot=None,
        collapse_risk=0.0,
        stable=True,
        global_stability_action="ignore",
        _epsilon=1.0,
        _cognitive_mode=None,
    )


def test_unavailable_validity_envelope_fails_closed(monkeypatch):
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate_stage.build_validity_envelope",
        lambda **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    ctx = _stage_ctx()
    pipeline = SimpleNamespace(
        theoretical_enforcement_mode="monitor",
        w_bound_tolerance=1.05,
        composite_rec_soft_threshold=0.0,
        composite_rec_strong_threshold=0.05,
    )

    GateStage().run(pipeline, ctx)

    assert ctx.gate_result is LyapunovVerdict.ABSTAIN
    trace = ctx.extra["verdict_transition_trace"]
    assert any(t["stage"] == "validity_envelope_unavailable" for t in trace)


# ---------------------------------------------------------------
# A4: switching safety envelope mode
# ---------------------------------------------------------------


def _envelope_ctx(**attrs):
    certificate = SimpleNamespace(domain_valid=True, is_projection_safe=True)
    base = {
        "scientific": None,
        "global_stability_metrics": None,
        "projection": None,
        "projection_certificate": certificate,
        "extra": {},
    }
    base.update(attrs)
    return SimpleNamespace(**base)


def _build(ctx, switching_safe: bool) -> None:
    build_validity_envelope(
        ctx=ctx,
        switching_safe=switching_safe,
        w_ratio=None,
        w_bound_tol=1.05,
        adaptive_metrics=None,
    )


def test_switching_soft_mode_is_observability_only():
    ctx = _envelope_ctx()
    _build(ctx, switching_safe=False)
    assert ctx.validity_envelope.valid is True
    assert "switching_soft_warning" in ctx.extra["fusion_reasons"]


def test_switching_enforce_mode_feeds_the_envelope():
    ctx = _envelope_ctx(switching_envelope_mode="enforce")
    _build(ctx, switching_safe=False)
    assert ctx.validity_envelope.valid is False
    assert ctx.validity_envelope.reason == "switching_violation"


def test_switching_enforce_mode_keeps_safe_switching_valid():
    ctx = _envelope_ctx(switching_envelope_mode="enforce")
    _build(ctx, switching_safe=True)
    assert ctx.validity_envelope.valid is True


def test_switching_unknown_mode_fails_closed_into_enforcement():
    ctx = _envelope_ctx(switching_envelope_mode="whatever")
    _build(ctx, switching_safe=False)
    assert ctx.validity_envelope.valid is False
    assert ctx.validity_envelope.reason == "switching_violation"


# ---------------------------------------------------------------
# A5: versioned severity table
# ---------------------------------------------------------------


def test_severity_table_is_versioned_and_covers_known_reasons():
    assert HARD_BLOCK_TABLE_VERSION
    for reason in ("global", "switching", "exponential_bound"):
        assert reason in DEFAULT_SEVERITY_TABLE


def test_known_reasons_do_not_hard_block_by_default():
    hard_block, hard_reason = resolve_hard_block(
        ["global", "switching", "exponential_bound"]
    )
    assert hard_block is False
    assert hard_reason == "global_switching_exponential_bound"


def test_unknown_reason_fails_closed_to_hard_block():
    hard_block, _ = resolve_hard_block(["global", "mystery"])
    assert hard_block is True


def test_empty_reasons_yield_no_block():
    assert resolve_hard_block([]) == (False, None)


def test_custom_table_can_escalate_a_reason():
    table = {"global": StabilitySeverity.HARD_BLOCK}
    hard_block, hard_reason = resolve_hard_block(["global"], table=table)
    assert hard_block is True
    assert hard_reason == "global"


def test_pipeline_records_table_version():
    ctx = CognitivePipelineContext(user_id="u", cognitive_input={}, timeline=[])
    CognitivePipeline().run(ctx)
    assert ctx.extra.get("hard_block_table_version") == HARD_BLOCK_TABLE_VERSION


# ---------------------------------------------------------------
# A6: pipeline-level monotonicity property
# ---------------------------------------------------------------

_STRICTNESS_BY_NAME = {
    str(verdict): rank for verdict, rank in VERDICT_STRICTNESS.items()
}

# Relaxation channels that are designed, traced and bounded:
# - global_policy_confirm: provenance-checked (lot A2);
# - input_risk_gate: pure-scalar grading, provenance-checked (lot A3);
# - recovery_* and apply_gate_policy: recovery reinterpretation, bounded
#   to the assessment phase by position;
# - answer_gate: the lighter ANSWER regime for answer-only turns.
SANCTIONED_RELAXATION_STAGES = frozenset(
    {
        "global_policy_confirm",
        "input_risk_gate",
        "recovery_to_allow",
        "recovery_to_confirmation",
        "apply_gate_policy",
        "answer_gate",
    }
)


class _StableCore:
    def compute(self, bundle):
        class Snapshot:
            collapse_risk = 0.2
            drift_score = 0.05
            regime = "stable"
            stable = True
            prev_lyap = 0.4
            cur_lyap = 0.2
            reflexive_state = {
                "stability_memory": 0.1,
                "structural_risk": 0.1,
                "regime_persistence": 0.1,
                "uncertainty_drift": 0.1,
            }

        return Snapshot()


@settings(max_examples=15, deadline=None)
@given(
    history=st.lists(
        st.floats(min_value=-10.0, max_value=10.0, allow_nan=False),
        max_size=6,
    ),
    action=st.sampled_from(["ignore", "confirm", "abstain"]),
    risk=st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0)),
)
def test_pipeline_trace_has_no_unsanctioned_relaxation(history, action, risk):
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=_StableCore())

    cognitive_input = {"risk": risk} if risk is not None else {}
    ctx = CognitivePipelineContext(
        user_id="u",
        cognitive_input=cognitive_input,
        timeline=[],
    )
    ctx.global_stability_action = action
    ctx.delta_w_history = list(history)

    pipeline.run(ctx)

    for transition in ctx.extra.get("verdict_transition_trace", []):
        before = _STRICTNESS_BY_NAME[transition["before"]]
        after = _STRICTNESS_BY_NAME[transition["after"]]
        if after < before:
            assert transition["stage"] in SANCTIONED_RELAXATION_STAGES, transition
