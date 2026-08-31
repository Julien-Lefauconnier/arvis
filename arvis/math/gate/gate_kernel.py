# arvis/math/gate/gate_kernel.py

from __future__ import annotations

from typing import Any

from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.math.lyapunov.lyapunov_gate import (
    LyapunovGateParams,
    LyapunovVerdict,
    lyapunov_gate,
)

from .gate_types import GateKernelInputs, GateKernelResult

# Collapse risk at or above this value refuses outright. The policy
# layer shares this constant: a recovery relaxation is never allowed to
# undo an abstention caused by the very signal it is bounded by
# (audit G2, 2026-08).
COLLAPSE_ABSTAIN_THRESHOLD: float = 0.8

# Minimum energy improvement that counts as recovery. Below this, a
# negative delta is numerical noise: it must not flip any decision.
# V lives in [0, 1] and W in the low single digits, so 1e-3 is a 0.1%
# improvement of the fast energy range (audit G2: a delta of -1e-18
# used to qualify as "recovery" and relax an ABSTAIN).
RECOVERY_MIN_IMPROVEMENT: float = 1e-3


def _detect_recovery(
    delta_w: float | None,
    w_prev: float | None,
    w_current: float | None,
    prev_lyap: Any | None,
    cur_lyap: Any | None,
) -> bool:
    """Whether the energy shows a real improvement between two steps.

    "Real" means beyond ``RECOVERY_MIN_IMPROVEMENT``: recovery is an
    input to a sanctioned verdict relaxation downstream, so its trigger
    must not be satisfiable by floating-point noise.
    """
    try:
        if delta_w is not None and delta_w < -RECOVERY_MIN_IMPROVEMENT:
            return True
        if prev_lyap is not None and cur_lyap is not None:
            if float(prev_lyap) - float(cur_lyap) > RECOVERY_MIN_IMPROVEMENT:
                return True
        if w_prev is not None and w_current is not None:
            if float(w_prev) - float(w_current) > RECOVERY_MIN_IMPROVEMENT:
                return True
    except (TypeError, ValueError):
        pass
    return False


def compute_gate_kernel(inputs: GateKernelInputs) -> GateKernelResult:
    reasons: list[str] = []

    # -----------------------------------------
    # Recovery detection (observability only)
    # -----------------------------------------
    # The kernel REPORTS recovery; it never relaxes its own verdict.
    # Whether a genuine recovery softens an abstention is the policy
    # layer's decision, bounded there by the collapse-risk threshold
    # (audit G2: the kernel used to downgrade ABSTAIN to
    # REQUIRE_CONFIRMATION itself, before the policy guard could see
    # the original verdict).
    recovery_detected = _detect_recovery(
        inputs.delta_w,
        inputs.w_prev,
        inputs.w_current,
        inputs.prev_lyap,
        inputs.cur_lyap,
    )

    # -----------------------------------------
    # Adaptive veto
    # -----------------------------------------
    adaptive_block = False
    if inputs.adaptive_available and inputs.adaptive_margin is not None:
        if inputs.adaptive_margin > 0:
            adaptive_block = True
            reasons.append("adaptive_instability")

    # -----------------------------------------
    # Pre-verdict: refusal first
    # -----------------------------------------
    # Refusal conditions are evaluated before any acceptance condition.
    # The previous ordering put the stable fast path first, so
    # stable=True plus an infinitesimal negative delta produced ALLOW
    # even at collapse_risk=0.99 in CRITICAL mode (audit G1).

    if inputs.stable is False:
        pre_verdict = LyapunovVerdict.ABSTAIN

    elif inputs.collapse_risk >= COLLAPSE_ABSTAIN_THRESHOLD:
        pre_verdict = LyapunovVerdict.ABSTAIN

    elif inputs.cognitive_mode == CognitiveMode.CRITICAL:
        pre_verdict = LyapunovVerdict.ABSTAIN

    # -------------------------------------------------
    # Minimal local stability fallback (acceptance)
    # -------------------------------------------------
    # Compliance YAML scenarios may inject a certified local delta_w
    # without full Lyapunov objects. With every refusal condition
    # clear, an explicitly stable system with a strictly decreasing
    # certified delta earns a local ALLOW pre-verdict.
    elif inputs.stable is True and inputs.delta_w is not None and inputs.delta_w < 0:
        pre_verdict = LyapunovVerdict.ALLOW

    elif inputs.cur_lyap is None:
        pre_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

    elif inputs.prev_lyap is None:
        pre_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

    else:
        params = LyapunovGateParams(eps_override=inputs.epsilon)

        pre_verdict = lyapunov_gate(
            previous=inputs.prev_lyap,
            current=inputs.cur_lyap,
            params=params,
            prev_slow=inputs.slow_prev,
            current_slow=inputs.slow_cur,
            prev_symbolic=inputs.symbolic_prev,
            current_symbolic=inputs.symbolic_cur,
        )

    # -----------------------------------------
    # Adaptive override (HARD)
    # -----------------------------------------
    if adaptive_block:
        final_verdict = LyapunovVerdict.ABSTAIN
        reasons.append("adaptive_hard_veto")

    else:
        final_verdict = pre_verdict

    # -----------------------------------------
    # Certificate (math only)
    # -----------------------------------------
    certificate = {
        "local": inputs.delta_w is not None,
        "global": bool(inputs.global_safe),
        "switching": bool(inputs.switching_safe),
        "delta_negative": (inputs.delta_w is not None and inputs.delta_w <= 0),
    }

    return GateKernelResult(
        pre_verdict=pre_verdict,
        final_verdict=final_verdict,
        recovery_detected=recovery_detected,
        adaptive_block=adaptive_block,
        reasons=reasons,
        certificate=certificate,
    )
