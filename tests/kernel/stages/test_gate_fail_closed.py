# tests/kernel/stages/test_gate_fail_closed.py

"""Fail-closed gate contract (F-002).

Two guarantees, tied together by one principle: a failing guarantee
mechanism can never relax.

1. An exception inside a verdict gate forces ABSTAIN instead of
   falling back to the upstream verdict, and safety computations that
   fail report unsafe instead of safe.
2. On normal paths, enforcement gates are monotone under the
   strictness order ALLOW < REQUIRE_CONFIRMATION < ABSTAIN: they can
   only escalate, never relax (property-based).

The ABSTAIN -> REQUIRE_CONFIRMATION transition of the global stability
policy under action="confirm" is provenance-checked since lot A2: it
only reinterprets an ABSTAIN produced by the global stability axis
itself and never relaxes a foreign veto (see verdict_order and
test_verdict_monotonic).
"""

from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.pipeline.stages.gate.enforcement import (
    apply_kappa_hard_block,
    apply_projection_enforcement,
)
from arvis.kernel.pipeline.stages.gate.stability import (
    apply_global_stability_policy,
    apply_validity_enforcement,
    compute_global_stability,
)
from arvis.kernel.pipeline.stages.gate.switching import compute_switching_safety
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

VERDICTS = [
    LyapunovVerdict.ALLOW,
    LyapunovVerdict.REQUIRE_CONFIRMATION,
    LyapunovVerdict.ABSTAIN,
]

STRICTNESS = {
    LyapunovVerdict.ALLOW: 0,
    LyapunovVerdict.REQUIRE_CONFIRMATION: 1,
    LyapunovVerdict.ABSTAIN: 2,
}


# ---------------------------------------------------------------
# Exception paths force ABSTAIN
# ---------------------------------------------------------------


class _BoomCert:
    @property
    def domain_valid(self):
        raise RuntimeError("boom")


class _BoomScientific:
    @property
    def adaptive(self):
        raise RuntimeError("boom")


class _BoomPolicyCtx:
    def __init__(self):
        self.extra = {}

    @property
    def global_stability_action(self):
        raise RuntimeError("boom")


def _last_transition(ctx_extra):
    trace = ctx_extra.get("verdict_transition_trace", [])
    assert trace, "fail-closed transition must be traced"
    return trace[-1]


@pytest.mark.parametrize("verdict", VERDICTS)
def test_projection_gate_exception_forces_abstain(verdict):
    ctx = SimpleNamespace(
        extra={},
        projection_certificate=_BoomCert(),
        projection_view=None,
        projected_state=None,
    )
    pipeline = SimpleNamespace(projection_boundary_threshold=0.1)
    out = apply_projection_enforcement(
        pipeline,
        ctx,
        verdict,
        GateOverrides(),
        delta_w=0.0,
        global_safe=True,
        switching_safe=True,
    )
    assert out is LyapunovVerdict.ABSTAIN
    last = _last_transition(ctx.extra)
    assert last["reason"] == "gate_exception"
    assert last["stage"] == "projection_gate_fail_closed"


@pytest.mark.parametrize("verdict", VERDICTS)
def test_kappa_gate_exception_forces_abstain(verdict):
    ctx = SimpleNamespace(extra={}, scientific=_BoomScientific())
    out = apply_kappa_hard_block(ctx, verdict)
    assert out is LyapunovVerdict.ABSTAIN
    assert _last_transition(ctx.extra)["reason"] == "gate_exception"


@pytest.mark.parametrize("verdict", VERDICTS)
def test_global_policy_exception_forces_abstain(verdict):
    ctx = _BoomPolicyCtx()
    out = apply_global_stability_policy(ctx, verdict, global_safe=False)
    assert out is LyapunovVerdict.ABSTAIN
    assert _last_transition(ctx.extra)["reason"] == "gate_exception"


@pytest.mark.parametrize("verdict", VERDICTS)
def test_validity_gate_exception_forces_abstain(verdict):
    ctx = SimpleNamespace(extra={}, scientific=_BoomScientific())
    out = apply_validity_enforcement(ctx, verdict, GateOverrides())
    assert out is LyapunovVerdict.ABSTAIN
    assert _last_transition(ctx.extra)["reason"] == "gate_exception"


# ---------------------------------------------------------------
# Failing safety computations report unsafe
# ---------------------------------------------------------------


def test_global_stability_guard_failure_reports_unsafe(monkeypatch):
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate.stability.GlobalStabilityGuard",
        lambda: SimpleNamespace(
            check=lambda history: (_ for _ in ()).throw(RuntimeError("boom"))
        ),
    )
    ctx = SimpleNamespace(extra={}, delta_w_history=[])
    assert compute_global_stability(ctx, 0.1) is False
    assert ctx.global_stability_safe is False


def test_switching_safety_failure_reports_unsafe(monkeypatch):
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate.switching.switching_condition",
        lambda runtime, params: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    ctx = SimpleNamespace(
        extra={},
        switching_runtime=object(),
        switching_params=object(),
    )
    assert compute_switching_safety(ctx, GateOverrides()) is False
    assert ctx.switching_safe is False


def test_switching_host_override_still_forces_safe(monkeypatch):
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.gate.switching.switching_condition",
        lambda runtime, params: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    ctx = SimpleNamespace(
        extra={},
        switching_runtime=object(),
        switching_params=object(),
    )
    overrides = GateOverrides(force_safe_switching=True)
    assert compute_switching_safety(ctx, overrides) is True


# ---------------------------------------------------------------
# Monotonicity property: enforcement never relaxes
# ---------------------------------------------------------------


@given(
    verdict=st.sampled_from(VERDICTS),
    domain_valid=st.booleans(),
    lyapunov_ok=st.booleans(),
    is_safe=st.booleans(),
    margin=st.one_of(
        st.none(),
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False),
    ),
    force_projection=st.booleans(),
    force_switching=st.booleans(),
)
def test_projection_enforcement_is_monotone(
    verdict,
    domain_valid,
    lyapunov_ok,
    is_safe,
    margin,
    force_projection,
    force_switching,
):
    cert = SimpleNamespace(
        domain_valid=domain_valid,
        margin_to_boundary=margin,
        is_projection_safe=is_safe,
        lyapunov_compatibility_ok=lyapunov_ok,
    )
    ctx = SimpleNamespace(
        extra={},
        projection_certificate=cert,
        projection_view=None,
        projected_state=None,
    )
    pipeline = SimpleNamespace(projection_boundary_threshold=0.1)
    out = apply_projection_enforcement(
        pipeline,
        ctx,
        verdict,
        GateOverrides(
            force_safe_projection=force_projection,
            force_safe_switching=force_switching,
        ),
        delta_w=0.0,
        global_safe=True,
        switching_safe=True,
    )
    assert STRICTNESS[out] >= STRICTNESS[verdict]


@given(
    verdict=st.sampled_from(VERDICTS),
    kappa_violation=st.booleans(),
)
def test_kappa_hard_block_is_monotone(verdict, kappa_violation):
    metrics = SimpleNamespace(kappa_violation=kappa_violation, kappa_gap=0.1)
    ctx = SimpleNamespace(extra={}, global_stability_metrics=metrics)
    out = apply_kappa_hard_block(ctx, verdict)
    assert STRICTNESS[out] >= STRICTNESS[verdict]


@given(
    verdict=st.sampled_from(VERDICTS),
    hard_block=st.booleans(),
    valid=st.booleans(),
)
def test_validity_enforcement_is_monotone(verdict, hard_block, valid):
    envelope = SimpleNamespace(hard_block=hard_block, valid=valid, reason="probe")
    ctx = SimpleNamespace(extra={}, validity_envelope=envelope)
    out = apply_validity_enforcement(ctx, verdict, GateOverrides())
    assert STRICTNESS[out] >= STRICTNESS[verdict]
