# tests/kernel/gate/test_gate_live_path_properties.py
"""Properties of the gate now that the measurement path is live (M3).

With the contraction monitor as the default core model, the gate
kernel's inputs are real measurements on every governed run. These
properties hold over the whole input space, not just the examples:

1. totality and refusal-first invariants of the kernel, for arbitrary
   realistic inputs (Hypothesis);
2. the declared-risk bands hold at EVERY trajectory depth: however the
   threaded science evolves, a pure declared-risk payload keeps its
   band (DM1, the measured axes never override the declared-risk
   authority);
3. a raising core model fails closed: the run aborts with the typed
   process error, it never degrades into an ALLOWED decision;
4. the policy layer's enforcement branches (strict veto, global
   instability actions) behave and never relax, closing the
   gate-policy coverage gap the audit measured at 59%.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from arvis import CognitiveOS, CognitiveOSConfig
from arvis.api.views.decision_status import DecisionStatus
from arvis.errors.runtime_execution import ProcessExecutionAborted
from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.math.gate.gate_kernel import (
    COLLAPSE_ABSTAIN_THRESHOLD,
    RECOVERY_MIN_IMPROVEMENT,
    compute_gate_kernel,
)
from arvis.math.gate.gate_policy import apply_gate_policy
from arvis.math.gate.gate_types import GateKernelInputs
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.lyapunov.verdict_order import strictness

# ---------------------------------------------------------------------------
# 1. Kernel totality and refusal-first invariants (Hypothesis)
# ---------------------------------------------------------------------------

_unit = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
_maybe_delta = st.one_of(
    st.none(), st.floats(min_value=-1.0, max_value=1.0, allow_nan=False)
)
_maybe_lyap = st.one_of(
    st.none(),
    st.builds(
        LyapunovState,
        budget_used=_unit,
        risk=_unit,
        uncertainty=_unit,
        governance=_unit,
    ),
)


@given(
    collapse_risk=_unit,
    stable=st.one_of(st.none(), st.booleans()),
    delta_w=_maybe_delta,
    prev_lyap=_maybe_lyap,
    cur_lyap=_maybe_lyap,
    mode=st.sampled_from(
        [CognitiveMode.NORMAL, CognitiveMode.SAFE, CognitiveMode.CRITICAL]
    ),
    adaptive_available=st.booleans(),
    adaptive_margin=st.one_of(
        st.none(), st.floats(min_value=-1.0, max_value=1.0, allow_nan=False)
    ),
)
def test_kernel_total_and_refusal_first(
    collapse_risk: float,
    stable: bool | None,
    delta_w: float | None,
    prev_lyap: LyapunovState | None,
    cur_lyap: LyapunovState | None,
    mode: CognitiveMode,
    adaptive_available: bool,
    adaptive_margin: float | None,
) -> None:
    result = compute_gate_kernel(
        GateKernelInputs(
            prev_lyap=prev_lyap,
            cur_lyap=cur_lyap,
            slow_prev=None,
            slow_cur=None,
            symbolic_prev=None,
            symbolic_cur=None,
            collapse_risk=collapse_risk,
            stable=stable,
            switching_safe=True,
            global_safe=True,
            delta_w=delta_w,
            w_prev=None,
            w_current=None,
            adaptive_margin=adaptive_margin,
            adaptive_available=adaptive_available,
            cognitive_mode=mode,
            epsilon=0.05,
        )
    )
    assert result.final_verdict in set(LyapunovVerdict)

    # Refusal-first: any refusal condition forces ABSTAIN, whatever the
    # acceptance evidence looks like.
    refused = (
        stable is False
        or collapse_risk >= COLLAPSE_ABSTAIN_THRESHOLD
        or mode == CognitiveMode.CRITICAL
        or (adaptive_available and adaptive_margin is not None and adaptive_margin > 0)
    )
    if refused:
        assert result.final_verdict is LyapunovVerdict.ABSTAIN

    # The kernel never relaxes: final is at least as strict as pre.
    assert strictness(result.final_verdict) >= strictness(result.pre_verdict)

    # Recovery is a report about magnitude, never satisfied by noise.
    if delta_w is not None and delta_w >= -RECOVERY_MIN_IMPROVEMENT:
        if prev_lyap is None and cur_lyap is None:
            assert not result.recovery_detected


# ---------------------------------------------------------------------------
# 2. Declared-risk bands hold at every trajectory depth (DM1)
# ---------------------------------------------------------------------------

_BANDS = {
    0.1: DecisionStatus.ALLOWED,
    0.5: DecisionStatus.REQUIRES_CONFIRMATION,
    0.92: DecisionStatus.BLOCKED,
}

# Vary the governance axis through the perceived intent so the threaded
# trajectory actually moves between turns.
_INTENTS = ["action_request", "informational_query", "search", "unknown"]


def test_declared_risk_bands_hold_at_every_trajectory_depth() -> None:
    state: dict[str, Any] | None = None
    for turn, intent in enumerate(_INTENTS * 2):
        # advance the trajectory with a varied cognitive turn
        extra: dict[str, Any] = {}
        if state is not None:
            extra["scientific_state"] = state
        CognitiveOS().run(
            user_id="traj",
            cognitive_input={"query": f"turn {turn}", "intent_type": intent},
            extra=extra,
        )
        state = extra.get("scientific_state_next")
        assert state is not None

        # at this depth, every declared-risk band must hold, threaded
        for declared, expected in _BANDS.items():
            band_extra: dict[str, Any] = {"scientific_state": state}
            view = CognitiveOS().run(
                user_id="traj",
                cognitive_input={"risk": declared},
                extra=band_extra,
            )
            assert view.status is expected, (
                f"turn {turn}: declared risk {declared} drifted to "
                f"{view.status.value}; the measured trajectory must never "
                "override the declared-risk authority (DM1)"
            )


# ---------------------------------------------------------------------------
# 3. A raising core model fails closed
# ---------------------------------------------------------------------------


class _ExplodingCore:
    def compute(self, bundle: Any, prior: Any = None) -> Any:
        raise RuntimeError("measurement failure")


def test_raising_core_model_fails_closed() -> None:
    engine = CognitiveOS(config=CognitiveOSConfig(core_model=_ExplodingCore()))
    with pytest.raises(ProcessExecutionAborted):
        engine.run(user_id="x", cognitive_input={"query": "hello"})


# ---------------------------------------------------------------------------
# 4. Policy-layer enforcement branches
# ---------------------------------------------------------------------------


def _ctx(**overrides: Any) -> SimpleNamespace:
    base: dict[str, Any] = dict(
        extra={},
        theoretical_enforcement_mode="monitor",
        global_stability_action="ignore",
        collapse_risk=0.0,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _envelope(hard_block: bool, hard_reason: str | None) -> SimpleNamespace:
    return SimpleNamespace(hard_block=hard_block, hard_reason=hard_reason)


def _kernel(recovery: bool = False) -> SimpleNamespace:
    return SimpleNamespace(recovery_detected=recovery)


def test_strict_mode_hard_block_vetoes() -> None:
    ctx = _ctx(theoretical_enforcement_mode="strict")
    out = apply_gate_policy(
        verdict=LyapunovVerdict.ALLOW,
        envelope=_envelope(True, "kappa_violation"),
        adaptive_metrics=None,
        ctx=ctx,
        kernel_result=_kernel(),
    )
    assert out is LyapunovVerdict.ABSTAIN
    assert "strict_veto_kappa_violation" in ctx.extra["fusion_reasons"]


@pytest.mark.parametrize(
    ("action", "verdict", "expected"),
    [
        ("abstain", LyapunovVerdict.ALLOW, LyapunovVerdict.ABSTAIN),
        ("confirm", LyapunovVerdict.ALLOW, LyapunovVerdict.REQUIRE_CONFIRMATION),
        # confirm is a floor: it must never relax a stricter verdict
        ("confirm", LyapunovVerdict.ABSTAIN, LyapunovVerdict.ABSTAIN),
        # ignore leaves the verdict to the other layers
        ("ignore", LyapunovVerdict.ALLOW, LyapunovVerdict.ALLOW),
    ],
)
def test_global_instability_actions_never_relax(
    action: str, verdict: LyapunovVerdict, expected: LyapunovVerdict
) -> None:
    out = apply_gate_policy(
        verdict=verdict,
        envelope=_envelope(True, "global_instability"),
        adaptive_metrics=None,
        ctx=_ctx(global_stability_action=action),
        kernel_result=_kernel(),
    )
    assert out is expected
    assert strictness(out) >= strictness(verdict)


def test_non_global_hard_block_records_and_passes() -> None:
    ctx = _ctx(global_stability_action="abstain")
    out = apply_gate_policy(
        verdict=LyapunovVerdict.REQUIRE_CONFIRMATION,
        envelope=_envelope(True, "kappa_violation"),
        adaptive_metrics=None,
        ctx=ctx,
        kernel_result=_kernel(),
    )
    assert out is LyapunovVerdict.REQUIRE_CONFIRMATION
    assert any(
        reason.startswith("hard_block_policy_")
        for reason in ctx.extra["fusion_reasons"]
    )
