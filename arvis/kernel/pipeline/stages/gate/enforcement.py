# arvis/kernel/pipeline/stages/gate/enforcement.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.pipeline.stages.gate.trace_helpers import record_verdict_transition
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def apply_projection_enforcement(
    pipeline: Any,
    ctx: Any,
    verdict: LyapunovVerdict,
    overrides: GateOverrides,
    delta_w: float | None,
    global_safe: bool,
    switching_safe: bool,
) -> LyapunovVerdict:
    try:
        projection_cert = getattr(ctx, "projection_certificate", None)
        projection_view = getattr(ctx, "projection_view", None)
        projected_state = getattr(ctx, "projected_state", None)

        if projection_cert is not None:
            domain_valid = bool(getattr(projection_cert, "domain_valid", False))
            margin = getattr(projection_cert, "margin_to_boundary", None)
            is_safe = bool(getattr(projection_cert, "is_projection_safe", False))
            lyapunov_compatible = bool(
                getattr(projection_cert, "lyapunov_compatibility_ok", True)
            )
        else:
            domain_valid = None
            margin = None
            is_safe = None
            lyapunov_compatible = None

        if projection_view is not None and isinstance(projection_view, dict):
            if "system_tension" not in projection_view:
                try:
                    if projected_state is not None:
                        projection_view["system_tension"] = float(
                            projected_state.primary_tension()
                        )
                except Exception:
                    projection_view["system_tension"] = 0.0

        projection_boundary_threshold = float(
            getattr(pipeline, "projection_boundary_threshold", 0.1)
        )

        if projection_cert is None:
            return verdict

        projection_reasons = ctx.extra.setdefault("fusion_reasons", [])
        ctx.extra["projection_domain_valid"] = bool(domain_valid)
        ctx.extra["projection_margin"] = margin
        ctx.extra["projection_safe"] = bool(is_safe)
        ctx.extra["projection_lyapunov_compatible"] = bool(lyapunov_compatible)

        if (
            domain_valid is False
            and not overrides.force_safe_projection
            and not overrides.disable_projection_hard_block
        ):
            if "projection_invalid" not in projection_reasons:
                projection_reasons.append("projection_invalid")
            record_verdict_transition(
                ctx,
                stage="projection_hard_block",
                before=verdict,
                after=LyapunovVerdict.ABSTAIN,
                reason="projection_invalid",
            )
            ctx.extra["projection_hard_block"] = True
            return LyapunovVerdict.ABSTAIN

        if lyapunov_compatible is False and not overrides.force_safe_projection:
            if "projection_lyapunov_incompatible" not in projection_reasons:
                projection_reasons.append("projection_lyapunov_incompatible")

            if verdict == LyapunovVerdict.ALLOW:
                record_verdict_transition(
                    ctx,
                    stage="projection_lyapunov_enforcement",
                    before=verdict,
                    after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                    reason="projection_lyapunov_incompatible",
                )
                verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

        if (
            not overrides.force_safe_projection
            and margin is not None
            and margin >= 0.0
            and margin < projection_boundary_threshold
        ):
            if "projection_boundary" not in projection_reasons:
                projection_reasons.append("projection_boundary")
            record_verdict_transition(
                ctx,
                stage="projection_boundary_enforcement",
                before=verdict,
                after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                reason="projection_boundary",
            )
            if verdict == LyapunovVerdict.ALLOW:
                verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

        projection_unstable_coupling = (not is_safe) and (
            (delta_w is not None and delta_w > 0.0)
            or (not bool(global_safe))
            or (not bool(switching_safe))
        )

        if projection_unstable_coupling and not overrides.force_safe_projection:
            if "projection_unsafe" not in projection_reasons:
                projection_reasons.append("projection_unsafe")

            if verdict == LyapunovVerdict.ALLOW:
                record_verdict_transition(
                    ctx,
                    stage="projection_unstable_coupling_soft",
                    before=verdict,
                    after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                    reason="projection_unsafe",
                )
                verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

        try:
            if projected_state is not None:
                coherence = projected_state.state_signals.get("coherence_score")
                if coherence is not None and coherence < 0.1:
                    ctx.extra.setdefault("fusion_reasons", []).append(
                        "low_coherence_signal"
                    )
        except Exception:
            pass

    except Exception:
        ctx.extra.setdefault("errors", []).append("projection_gate_adjustment_failure")
    return verdict


def apply_kappa_hard_block(ctx: Any, verdict: LyapunovVerdict) -> LyapunovVerdict:
    try:
        metrics = getattr(ctx, "global_stability_metrics", None)
        if metrics is not None and getattr(metrics, "kappa_violation", False):
            reasons = ctx.extra.setdefault("fusion_reasons", [])
            if "kappa_violation" not in reasons:
                reasons.append("kappa_violation")
            record_verdict_transition(
                ctx,
                stage="kappa_hard_block",
                before=verdict,
                after=LyapunovVerdict.ABSTAIN,
                reason="kappa_violation",
            )
            ctx.extra["kappa_hard_block"] = True
            ctx.extra["kappa_gap"] = getattr(metrics, "kappa_gap", None)
            verdict = LyapunovVerdict.ABSTAIN
    except Exception:
        pass
    return verdict
