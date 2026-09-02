# tests/kernel/gate/test_verdict_transition_trace.py
"""The verdict transition trace records only what actually happened.

Campaign GATE-SEM (LOT G5, audit P1-2, 2026-09-02). The trace is the
audit surface PATH_TO_ALLOW documents as "every tightening, with its
stage" and it recorded transitions that never happened: the
projection boundary stage logged ``ABSTAIN -> REQUIRE_CONFIRMATION``
unconditionally on turns whose verdict never moved (431 entries per
corpus), and the adaptive vetoes logged ``ABSTAIN -> ABSTAIN`` no-ops
(2x1139 on D-1.0). Same defect class as DM-P2: the audit trail
contradicted the decision.

The invariant pinned here:

- A trace entry with ``after == before`` is only ever an explicit
  event record (a denied relaxation: stage suffix ``_denied`` or
  ``_relaxation_blocked``). Every other entry is a real change.
- An entry whose ``after`` is SOFTER than ``before`` (a recorded
  relaxation) only ever comes from the sanctioned relaxation stages;
  any new relaxation site must be added here deliberately.
"""

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.pipeline.stages.gate.adaptive import apply_final_adaptive_veto
from arvis.kernel.pipeline.stages.gate.enforcement import (
    apply_projection_enforcement,
)
from arvis.kernel.pipeline.stages.gate.memory_policy import apply_memory_policy
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.lyapunov.verdict_order import is_relaxation
from tests.fixtures.builders.context_builder import build_test_context

# Stages allowed to record an entry whose after == before: explicit
# denial / blocked-attempt events, not transitions.
EVENT_STAGE_SUFFIXES = ("_denied", "_relaxation_blocked")

# The only stages sanctioned to RECORD a relaxation (each one is
# provenance- or regime-guarded in code). A relaxation entry from any
# other stage is a defect.
SANCTIONED_RELAXATION_STAGES = frozenset(
    {
        "input_risk_gate",
        "global_policy_confirm",
        "recovery_to_confirmation",
        "answer_gate",
    }
)

_VERDICTS = {str(v): v for v in LyapunovVerdict}


def assert_trace_is_honest(trace: list[dict[str, Any]]) -> None:
    """Shared invariant: no phantom transition, no rogue relaxation."""
    for entry in trace:
        stage = str(entry.get("stage", ""))
        before = _VERDICTS[str(entry["before"])]
        after = _VERDICTS[str(entry["after"])]

        if after == before:
            assert stage.endswith(EVENT_STAGE_SUFFIXES), (
                f"phantom transition: stage {stage!r} recorded a no-op "
                f"{before} -> {after} but is not an event stage"
            )
        elif is_relaxation(before, after):
            assert stage in SANCTIONED_RELAXATION_STAGES, (
                f"unsanctioned relaxation recorded by stage {stage!r}: "
                f"{before} -> {after}"
            )


def _trace_of(ctx: Any) -> list[dict[str, Any]]:
    return list(ctx.journal.verdict_transition_trace)


class _Certificate:
    domain_valid = True
    margin_to_boundary = 0.05  # inside the boundary band (< 0.1)
    is_projection_safe = True
    lyapunov_compatibility_ok = True


def test_projection_boundary_records_nothing_on_a_non_allow_verdict() -> None:
    """A boundary-proximity turn whose verdict is already ABSTAIN must
    not log an ``ABSTAIN -> REQUIRE_CONFIRMATION`` that never happened."""
    ctx = build_test_context()
    ctx.projection.certificate = _Certificate()

    verdict = apply_projection_enforcement(
        pipeline=object(),
        ctx=ctx,
        verdict=LyapunovVerdict.ABSTAIN,
        overrides=GateOverrides(),
        delta_w=-0.02,
        global_safe=True,
        switching_safe=True,
    )

    assert verdict is LyapunovVerdict.ABSTAIN
    assert "projection_boundary" in ctx.journal.fusion_reasons
    boundary_entries = [
        e for e in _trace_of(ctx) if e["stage"] == "projection_boundary_enforcement"
    ]
    assert boundary_entries == []


def test_projection_boundary_still_records_the_real_transition() -> None:
    ctx = build_test_context()
    ctx.projection.certificate = _Certificate()

    verdict = apply_projection_enforcement(
        pipeline=object(),
        ctx=ctx,
        verdict=LyapunovVerdict.ALLOW,
        overrides=GateOverrides(),
        delta_w=-0.02,
        global_safe=True,
        switching_safe=True,
    )

    assert verdict is LyapunovVerdict.REQUIRE_CONFIRMATION
    boundary_entries = [
        e for e in _trace_of(ctx) if e["stage"] == "projection_boundary_enforcement"
    ]
    assert len(boundary_entries) == 1
    assert boundary_entries[0]["before"] == str(LyapunovVerdict.ALLOW)
    assert boundary_entries[0]["after"] == str(LyapunovVerdict.REQUIRE_CONFIRMATION)


def test_final_adaptive_veto_records_no_noop_but_keeps_its_flag() -> None:
    """An adaptive veto on an already-ABSTAIN verdict is a no-op for
    the trace, but the ``hard_adaptive_veto`` flag other layers
    consult (global-policy relaxation guard) must keep being set."""
    ctx = build_test_context()
    unstable = AdaptiveSnapshot(
        kappa_eff=0.05,
        margin=0.4,
        regime="unstable",
        available=True,
    )

    verdict = apply_final_adaptive_veto(ctx, LyapunovVerdict.ABSTAIN, unstable)

    assert verdict is LyapunovVerdict.ABSTAIN
    assert ctx.journal.hard_adaptive_veto is True
    assert ctx.extra["_hard_adaptive_veto"] is True
    veto_entries = [
        e for e in _trace_of(ctx) if e["stage"] == "final_adaptive_hard_veto"
    ]
    assert veto_entries == []


def test_final_adaptive_veto_records_the_real_transition() -> None:
    ctx = build_test_context()
    unstable = AdaptiveSnapshot(
        kappa_eff=0.05,
        margin=0.4,
        regime="unstable",
        available=True,
    )

    verdict = apply_final_adaptive_veto(
        ctx, LyapunovVerdict.REQUIRE_CONFIRMATION, unstable
    )

    assert verdict is LyapunovVerdict.ABSTAIN
    veto_entries = [
        e for e in _trace_of(ctx) if e["stage"] == "final_adaptive_hard_veto"
    ]
    assert len(veto_entries) == 1
    assert veto_entries[0]["before"] == str(LyapunovVerdict.REQUIRE_CONFIRMATION)


def test_memory_hard_block_records_no_noop_on_abstain() -> None:
    ctx = build_test_context()
    ctx.decision_layer.bundle = type(
        "Bundle", (), {"memory_features": {"memory_pressure": 0.9}}
    )()

    verdict = apply_memory_policy(ctx, LyapunovVerdict.ABSTAIN)

    assert verdict is LyapunovVerdict.ABSTAIN
    assert "memory_pressure_hard" in ctx.journal.fusion_reasons
    block_entries = [e for e in _trace_of(ctx) if e["stage"] == "memory_hard_block"]
    assert block_entries == []


def test_memory_hard_block_records_the_real_transition() -> None:
    ctx = build_test_context()
    ctx.decision_layer.bundle = type(
        "Bundle", (), {"memory_features": {"memory_pressure": 0.9}}
    )()

    verdict = apply_memory_policy(ctx, LyapunovVerdict.ALLOW)

    assert verdict is LyapunovVerdict.ABSTAIN
    block_entries = [e for e in _trace_of(ctx) if e["stage"] == "memory_hard_block"]
    assert len(block_entries) == 1
    assert block_entries[0]["before"] == str(LyapunovVerdict.ALLOW)


def test_smoke_corpus_traces_are_honest() -> None:
    """Every measured turn of the closed-loop smoke corpus leaves a
    trace whose entries are real changes or explicit event records.

    RED on the pre-campaign tree: the projection boundary stage and
    both adaptive vetoes recorded phantom entries on most turns."""
    from validation.m10.corpus import build_smoke_corpus
    from validation.m10.runner import run_trajectory

    corpus = build_smoke_corpus()
    saw_entries = False
    for spec in corpus.trajectories:
        for measurement in run_trajectory(spec):
            transitions = [dict(t) for t in measurement.verdict_transitions]
            saw_entries = saw_entries or bool(transitions)
            assert_trace_is_honest(transitions)
    assert saw_entries, "smoke corpus produced no transitions at all"
