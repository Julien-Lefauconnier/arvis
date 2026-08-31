# arvis/math/gate/gate_policy.py

from __future__ import annotations

from typing import Any

from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.gate.gate_kernel import COLLAPSE_ABSTAIN_THRESHOLD
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.lyapunov.verdict_order import max_strictness


def apply_gate_policy(
    verdict: LyapunovVerdict,
    envelope: Any,
    adaptive_metrics: AdaptiveSnapshot | None,
    ctx: Any,
    kernel_result: Any,
) -> LyapunovVerdict:
    """
    Centralized policy layer.

    Responsibilities:
    - strict theoretical enforcement
    - global instability policy
    - recovery invariant
    """

    reasons = ctx.extra.setdefault("fusion_reasons", [])

    # -----------------------------------------
    # 1. STRICT MODE
    # -----------------------------------------
    mode = getattr(ctx, "theoretical_enforcement_mode", None) or getattr(
        getattr(ctx, "pipeline", None), "theoretical_enforcement_mode", "monitor"
    )

    if mode == "strict" and envelope.hard_block:
        reasons.append(f"strict_veto_{envelope.hard_reason}")
        return LyapunovVerdict.ABSTAIN

    # -----------------------------------------
    # 2. GLOBAL POLICY
    # -----------------------------------------
    action = getattr(ctx, "global_stability_action", "ignore")

    if envelope.hard_block:
        if "global" in (envelope.hard_reason or ""):
            if action == "abstain":
                reasons.append("global_instability_abstain")
                return LyapunovVerdict.ABSTAIN
            elif action == "confirm":
                reasons.append("global_instability_confirm")
                # Monotone (F-001): confirm is a floor, it never
                # overwrites a stricter verdict.
                return max_strictness(verdict, LyapunovVerdict.REQUIRE_CONFIRMATION)
        else:
            reasons.append(f"hard_block_policy_{action}_{envelope.hard_reason}")

    # -----------------------------------------
    # 3. RECOVERY RELAXATION (bounded)
    # -----------------------------------------
    # The one sanctioned relaxation at this layer: a genuine recovery
    # (thresholded upstream, see RECOVERY_MIN_IMPROVEMENT) softens an
    # ABSTAIN to REQUIRE_CONFIRMATION: a human re-enters the loop, the
    # system does not self-approve. It is bounded by the SAME threshold
    # that turns collapse risk into an abstention: at or above it, the
    # relaxation would undo the very signal that caused the refusal, so
    # nothing is relaxed (audit G2: the guard sat at 0.9 while the
    # abstain trigger sat at 0.8, and the kernel had already downgraded
    # the verdict before this guard could see it).
    if kernel_result.recovery_detected or ctx.extra.get("recovery_detected"):
        adaptive_margin = None
        if adaptive_metrics and adaptive_metrics.is_available:
            adaptive_margin = adaptive_metrics.margin

        adaptive_block = adaptive_margin is not None and adaptive_margin > 0

        if not adaptive_block:
            if verdict == LyapunovVerdict.ABSTAIN:
                collapse = float(getattr(ctx, "collapse_risk", 0.0))
                if collapse < COLLAPSE_ABSTAIN_THRESHOLD:
                    reasons.append("recovery_hard_override")
                    return LyapunovVerdict.REQUIRE_CONFIRMATION

    return verdict
