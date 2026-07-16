# tests/kernel/gate/test_input_risk_gate.py
"""Governed input-risk policy: pure-logic unit tests.

These pin the three-band mapping and the gate helper behaviour deterministically
(no full-pipeline run). End-to-end grading is demonstrated by the examples
(risk 0.10 / 0.50 / 0.90).
"""

from types import SimpleNamespace

from arvis.kernel.gate.input_risk import (
    is_pure_risk_payload,
    read_input_risk,
    resolve_input_risk_verdict,
)
from arvis.kernel.pipeline.stages.gate.input_risk_gate import apply_input_risk_gate
from arvis.kernel.pipeline.stages.gate.trace_helpers import VERDICT_PROVENANCE_KEY
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

# --- read_input_risk: only a numeric top-level "risk" qualifies ---


def test_read_top_level_numeric_risk():
    assert read_input_risk({"risk": 0.9}) == 0.9
    assert read_input_risk({"risk": 0}) == 0.0
    assert read_input_risk({"risk": 1.5}) == 1.0  # clamped


def test_read_ignores_nested_and_non_numeric():
    # Nested numeric_signals must NOT be read (compliance/observational path).
    assert read_input_risk({"numeric_signals": {"risk": 0.5}}) is None
    assert read_input_risk({"risk": "invalid"}) is None
    assert read_input_risk({"risk": True}) is None  # bool excluded
    assert read_input_risk({}) is None
    assert read_input_risk(None) is None


# --- resolve_input_risk_verdict: three bands ---


def test_three_band_mapping():
    assert resolve_input_risk_verdict(0.10) == "allow"
    assert resolve_input_risk_verdict(0.39) == "allow"
    assert resolve_input_risk_verdict(0.40) == "require_confirmation"
    assert resolve_input_risk_verdict(0.55) == "require_confirmation"
    assert resolve_input_risk_verdict(0.79) == "require_confirmation"
    assert resolve_input_risk_verdict(0.80) == "abstain"
    assert resolve_input_risk_verdict(0.98) == "abstain"


# --- apply_input_risk_gate: override behaviour ---


def _ctx(cognitive_input, extra=None):
    return SimpleNamespace(
        cognitive_input=cognitive_input,
        extra=extra if extra is not None else {},
    )


def test_gate_no_top_level_risk_is_passthrough():
    ctx = _ctx({"numeric_signals": {"risk": 0.9}})
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ALLOW)
    assert out == LyapunovVerdict.ALLOW  # unchanged


def test_gate_grades_from_input_risk():
    assert (
        apply_input_risk_gate(_ctx({"risk": 0.1}), LyapunovVerdict.ABSTAIN)
        == LyapunovVerdict.ALLOW
    )
    assert (
        apply_input_risk_gate(_ctx({"risk": 0.5}), LyapunovVerdict.ALLOW)
        == LyapunovVerdict.REQUIRE_CONFIRMATION
    )
    assert (
        apply_input_risk_gate(_ctx({"risk": 0.9}), LyapunovVerdict.ALLOW)
        == LyapunovVerdict.ABSTAIN
    )


def test_gate_never_relaxes_kappa_hard_block():
    ctx = _ctx({"risk": 0.1}, extra={"kappa_hard_block": True})
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ABSTAIN)
    assert out == LyapunovVerdict.ABSTAIN  # real hard block wins over low risk


def test_gate_never_relaxes_real_veto_reason():
    # A real safety veto in the fusion reasons is not relaxed by a low risk.
    ctx = _ctx(
        {"risk": 0.1},
        extra={"fusion_reasons": ["adaptive_instability_veto"]},
    )
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ABSTAIN)
    assert out == LyapunovVerdict.ABSTAIN


def test_gate_supersedes_projection_artifact_and_keeps_ir_consistent():
    # The sparse-projection veto is superseded when the policy governs ALLOW,
    # and a single governing reason is recorded (IR stays consistent).
    ctx = _ctx(
        {"risk": 0.1},
        extra={"fusion_reasons": ["projection_invalid", "projection_boundary"]},
    )
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ABSTAIN)

    assert out == LyapunovVerdict.ALLOW
    reasons = ctx.extra["fusion_reasons"]
    assert "projection_invalid" not in reasons
    assert "projection_boundary" not in reasons
    assert "input_risk_gate" in reasons
    assert len(reasons) >= 1  # never empty -> reason_codes validation holds


def test_gate_relax_denied_by_non_artifact_provenance():
    # A traced hardening outside the sparse-projection artifact set is a
    # real veto: a declared low risk never relaxes it (audit F-006).
    ctx = _ctx(
        {"risk": 0.1},
        extra={VERDICT_PROVENANCE_KEY: {"ABSTAIN": "memory_hard_block"}},
    )
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ABSTAIN)
    assert out == LyapunovVerdict.ABSTAIN
    trace = ctx.extra["verdict_transition_trace"]
    assert trace[-1]["stage"] == "input_risk_relax_denied"


def test_gate_relaxes_sparse_projection_artifact():
    ctx = _ctx(
        {"risk": 0.1},
        extra={VERDICT_PROVENANCE_KEY: {"ABSTAIN": "projection_hard_block"}},
    )
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ABSTAIN)
    assert out == LyapunovVerdict.ALLOW


def test_gate_exception_forces_abstain():
    class _BoomInputCtx:
        def __init__(self):
            self.extra = {}

        @property
        def cognitive_input(self):
            raise RuntimeError("boom")

    ctx = _BoomInputCtx()
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ALLOW)
    assert out is LyapunovVerdict.ABSTAIN
    trace = ctx.extra["verdict_transition_trace"]
    assert trace[-1]["stage"] == "input_risk_fail_closed"
    assert trace[-1]["reason"] == "gate_exception"


def test_gate_records_input_risk_in_extra():
    ctx = _ctx({"risk": 0.5})
    apply_input_risk_gate(ctx, LyapunovVerdict.ALLOW)
    assert ctx.extra["input_risk"] == 0.5
    # governing reason recorded even without prior fusion reasons
    assert "input_risk_gate" in ctx.extra["fusion_reasons"]


# --- F-001-a5: pure-scalar precondition and harden-only doctrine ---


def test_is_pure_risk_payload():
    assert is_pure_risk_payload({"risk": 0.5}) is True
    assert is_pure_risk_payload({"risk": 0}) is True
    assert is_pure_risk_payload({"risk": 0.1, "action": "x"}) is False
    assert is_pure_risk_payload({"action": "x"}) is False
    assert is_pure_risk_payload({"risk": "invalid"}) is False
    assert is_pure_risk_payload({"risk": True}) is False
    assert is_pure_risk_payload({}) is False
    assert is_pure_risk_payload(None) is False


def test_gate_mixed_payload_never_relaxes():
    # Audit F-001-a5 reproduction: a mixed payload with content produces a
    # projection ABSTAIN whose provenance is in the relaxable artifact set;
    # a declared low risk must NOT relax it.
    ctx = _ctx(
        {"action": "delete_everything", "risk": 0.1},
        extra={VERDICT_PROVENANCE_KEY: {"ABSTAIN": "projection_hard_block"}},
    )
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ABSTAIN)
    assert out == LyapunovVerdict.ABSTAIN


def test_gate_mixed_payload_hardens_and_traces():
    # Harden-only path: max_strictness, traced, governing signal appended.
    ctx = _ctx({"action": "x", "risk": 0.9})
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ALLOW)
    assert out == LyapunovVerdict.ABSTAIN
    trace = ctx.extra["verdict_transition_trace"]
    assert trace[-1]["stage"] == "input_risk_harden"
    assert "input_risk_harden" in ctx.extra["fusion_reasons"]


def test_gate_mixed_payload_low_risk_keeps_verdict_and_reasons():
    # No relaxation, no supersession: the existing reasons stay intact.
    ctx = _ctx(
        {"query": "approve", "risk": 0.1},
        extra={"fusion_reasons": ["projection_invalid"]},
    )
    out = apply_input_risk_gate(ctx, LyapunovVerdict.REQUIRE_CONFIRMATION)
    assert out == LyapunovVerdict.REQUIRE_CONFIRMATION
    assert ctx.extra["fusion_reasons"] == ["projection_invalid"]


def test_gate_mixed_payload_medium_risk_hardens_allow():
    ctx = _ctx({"request_id": "REQ-1", "risk": 0.5})
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ALLOW)
    assert out == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_gate_harden_only_mode_blocks_pure_payload_relaxation():
    # Production posture: even a pure {"risk": x} payload never relaxes.
    ctx = _ctx(
        {"risk": 0.1},
        extra={VERDICT_PROVENANCE_KEY: {"ABSTAIN": "projection_hard_block"}},
    )
    ctx.input_risk_mode = "harden_only"
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ABSTAIN)
    assert out == LyapunovVerdict.ABSTAIN


def test_gate_harden_only_mode_still_hardens_pure_payload():
    # Decision 2.2-a: hardening by a pure payload stays available in
    # production; only relaxation is forbidden.
    ctx = _ctx({"risk": 0.9})
    ctx.input_risk_mode = "harden_only"
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ALLOW)
    assert out == LyapunovVerdict.ABSTAIN


def test_gate_unknown_mode_fails_closed_to_harden_only():
    ctx = _ctx(
        {"risk": 0.1},
        extra={VERDICT_PROVENANCE_KEY: {"ABSTAIN": "projection_hard_block"}},
    )
    ctx.input_risk_mode = "definitely_not_a_mode"
    out = apply_input_risk_gate(ctx, LyapunovVerdict.ABSTAIN)
    assert out == LyapunovVerdict.ABSTAIN
