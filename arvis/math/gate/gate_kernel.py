# arvis/math/gate/gate_kernel.py

from __future__ import annotations

from typing import Optional, Any, List

from arvis.math.lyapunov.lyapunov_gate import (
    lyapunov_gate,
    LyapunovVerdict,
    LyapunovGateParams,
)

from arvis.math.control.eps_adaptive import CognitiveMode
from .gate_types import GateKernelInputs, GateKernelResult


def _detect_recovery(
    delta_w: Optional[float],
    w_prev: Optional[float],
    w_current: Optional[float],
    prev_lyap: Optional[Any],
    cur_lyap: Optional[Any],
) -> bool:
    try:
        if delta_w is not None and delta_w < 0:
            return True
        if prev_lyap is not None and cur_lyap is not None:
            if float(cur_lyap) < float(prev_lyap):
                return True
        if w_prev is not None and w_current is not None:
            if float(w_current) < float(w_prev):
                return True
    except Exception:
        pass
    return False


def compute_gate_kernel(inputs: GateKernelInputs) -> GateKernelResult:
    reasons: List[str] = []

    # -----------------------------------------
    # Recovery detection
    # -----------------------------------------
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
    # Pre-verdict (Lyapunov local)
    # -----------------------------------------
    if inputs.stable is False:
        pre_verdict = LyapunovVerdict.ABSTAIN

    elif inputs.collapse_risk >= 0.8:
        pre_verdict = LyapunovVerdict.ABSTAIN

    elif inputs.cognitive_mode == CognitiveMode.CRITICAL:
        pre_verdict = LyapunovVerdict.ABSTAIN

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
    # Recovery soft override
    # -----------------------------------------
    if recovery_detected and not adaptive_block:
        if final_verdict == LyapunovVerdict.ABSTAIN:
            final_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
            reasons.append("recovery_override")

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
