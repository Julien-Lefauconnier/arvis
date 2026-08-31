# tests/math/gate/test_gate_safety_ordering.py
"""Refusal-first ordering and bounded recovery in the gate kernel stack.

These tests pin the safety properties the gate documents but did not
hold (audit findings G1 and G2, 2026-08):

- G1: the ``stable=True`` fast path short-circuited the collapse-risk
  and CRITICAL-mode refusal branches, so an infinitesimal energy
  decrease produced ALLOW at ``collapse_risk=0.99`` in CRITICAL mode.
- G2: any energy decrease, down to ``-1e-18``, was treated as
  "recovery" and relaxed ABSTAIN to REQUIRE_CONFIRMATION inside the
  kernel, before the policy layer's collapse-risk guard could see the
  original ABSTAIN.

The properties enforced here:

1. Refusal conditions are evaluated before any acceptance condition.
2. The kernel never relaxes its own verdict; it only reports
   ``recovery_detected`` for the policy layer.
3. Recovery detection requires a real improvement
   (``RECOVERY_MIN_IMPROVEMENT``), never numerical noise.
4. The policy-layer recovery relaxation is bounded by the same
   threshold that causes the collapse-risk ABSTAIN: at or above
   ``collapse_risk = 0.8`` nothing is relaxed.
5. Recovery never relaxes past REQUIRE_CONFIRMATION: a recovering
   system may stop refusing, it does not self-approve.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from arvis.kernel.pipeline.stages.gate.decision_stack import apply_recovery_override
from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.math.gate.gate_kernel import RECOVERY_MIN_IMPROVEMENT, compute_gate_kernel
from arvis.math.gate.gate_policy import apply_gate_policy
from arvis.math.gate.gate_types import GateKernelInputs
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _inputs(**overrides: Any) -> GateKernelInputs:
    base: dict[str, Any] = dict(
        prev_lyap=None,
        cur_lyap=None,
        slow_prev=None,
        slow_cur=None,
        symbolic_prev=None,
        symbolic_cur=None,
        collapse_risk=0.0,
        stable=None,
        switching_safe=True,
        global_safe=True,
        delta_w=None,
        w_prev=None,
        w_current=None,
        adaptive_margin=None,
        adaptive_available=False,
        cognitive_mode=CognitiveMode.NORMAL,
        epsilon=0.05,
    )
    base.update(overrides)
    return GateKernelInputs(**base)


# ---------------------------------------------------------------------------
# G1: refusal-first ordering
# ---------------------------------------------------------------------------


def test_collapse_risk_refusal_beats_stable_fast_path() -> None:
    result = compute_gate_kernel(
        _inputs(stable=True, delta_w=-1e-12, collapse_risk=0.99)
    )
    assert result.final_verdict is LyapunovVerdict.ABSTAIN, (
        "collapse_risk=0.99 must refuse regardless of the stable flag; "
        f"got {result.final_verdict}"
    )


def test_critical_mode_refusal_beats_stable_fast_path() -> None:
    result = compute_gate_kernel(
        _inputs(stable=True, delta_w=-0.05, cognitive_mode=CognitiveMode.CRITICAL)
    )
    assert result.final_verdict is LyapunovVerdict.ABSTAIN, (
        "CRITICAL mode must refuse regardless of the stable flag; "
        f"got {result.final_verdict}"
    )


def test_stable_fast_path_still_allows_in_nominal_conditions() -> None:
    """The compliance fast path survives the reorder: certified local
    decrease with low collapse risk in NORMAL mode is still ALLOW."""
    result = compute_gate_kernel(_inputs(stable=True, delta_w=-0.3, collapse_risk=0.1))
    assert result.final_verdict is LyapunovVerdict.ALLOW


# ---------------------------------------------------------------------------
# G2: the kernel reports recovery, it never relaxes
# ---------------------------------------------------------------------------


def test_kernel_does_not_relax_collapse_abstain_on_noise() -> None:
    result = compute_gate_kernel(_inputs(collapse_risk=0.99, delta_w=-1e-18))
    assert result.final_verdict is LyapunovVerdict.ABSTAIN
    assert not result.recovery_detected, (
        "an energy decrease of 1e-18 is numerical noise, not recovery"
    )


def test_kernel_does_not_relax_collapse_abstain_on_real_improvement() -> None:
    result = compute_gate_kernel(_inputs(collapse_risk=0.99, delta_w=-0.5))
    assert result.recovery_detected, "delta_w=-0.5 is a real improvement"
    assert result.final_verdict is LyapunovVerdict.ABSTAIN, (
        "relaxation is the policy layer's decision, bounded by "
        "collapse_risk; the kernel must report and hold"
    )


def test_recovery_detection_threshold_on_w_pair() -> None:
    noise = compute_gate_kernel(
        _inputs(collapse_risk=0.99, w_prev=1.0, w_current=1.0 - 1e-15)
    )
    real = compute_gate_kernel(
        _inputs(
            collapse_risk=0.99,
            w_prev=1.0,
            w_current=1.0 - 10 * RECOVERY_MIN_IMPROVEMENT,
        )
    )
    assert not noise.recovery_detected
    assert real.recovery_detected


# ---------------------------------------------------------------------------
# G2: policy-layer relaxation is bounded by the abstain threshold
# ---------------------------------------------------------------------------


def _policy_ctx(collapse_risk: float) -> SimpleNamespace:
    return SimpleNamespace(
        extra={},
        theoretical_enforcement_mode="monitor",
        global_stability_action="ignore",
        collapse_risk=collapse_risk,
    )


def _envelope(hard_block: bool = False, hard_reason: str | None = None) -> Any:
    return SimpleNamespace(hard_block=hard_block, hard_reason=hard_reason)


def _kernel_result(recovery: bool) -> Any:
    return SimpleNamespace(recovery_detected=recovery)


def test_policy_recovery_bounded_by_collapse_threshold() -> None:
    out = apply_gate_policy(
        verdict=LyapunovVerdict.ABSTAIN,
        envelope=_envelope(),
        adaptive_metrics=None,
        ctx=_policy_ctx(collapse_risk=0.85),
        kernel_result=_kernel_result(recovery=True),
    )
    assert out is LyapunovVerdict.ABSTAIN, (
        "collapse_risk >= 0.8 causes the ABSTAIN; recovery must not undo "
        "the very signal that triggered the refusal"
    )


def test_policy_recovery_relaxes_below_collapse_threshold() -> None:
    out = apply_gate_policy(
        verdict=LyapunovVerdict.ABSTAIN,
        envelope=_envelope(),
        adaptive_metrics=None,
        ctx=_policy_ctx(collapse_risk=0.3),
        kernel_result=_kernel_result(recovery=True),
    )
    assert out is LyapunovVerdict.REQUIRE_CONFIRMATION, (
        "below the abstain threshold, a genuine recovery keeps a human "
        "in the loop instead of refusing outright"
    )


# ---------------------------------------------------------------------------
# G2: recovery never relaxes past REQUIRE_CONFIRMATION
# ---------------------------------------------------------------------------


def test_stage_recovery_caps_at_require_confirmation() -> None:
    ctx = SimpleNamespace(
        extra={},
        validity_envelope=SimpleNamespace(valid=True),
        collapse_risk=0.2,
    )
    out = apply_recovery_override(
        ctx=ctx,
        verdict=LyapunovVerdict.ABSTAIN,
        recovery_detected=True,
        kernel_result=_kernel_result(recovery=True),
        adaptive_metrics=None,
    )
    assert out is LyapunovVerdict.REQUIRE_CONFIRMATION, (
        f"a recovering system stops refusing; it does not self-approve (got {out})"
    )
