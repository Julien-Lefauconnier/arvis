# arvis/kernel/pipeline/stages/gate/adaptive.py

from __future__ import annotations

from typing import Any

from arvis.errors.manager import ErrorManager
from arvis.kernel.pipeline.context.journal_context import (
    fusion_reasons_of,
    journal_of,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    adaptive_snapshot,
    set_adaptive_snapshot,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    scientific as scientific_of,
)
from arvis.kernel.pipeline.stages.gate.trace_helpers import (
    record_verdict_transition,
)
from arvis.math.adaptive.adaptive_runtime_observer import (
    AdaptiveRuntimeObserver,
)
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.adaptive.kappa_bands import kappa_band as kappa_band_of
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def compute_adaptive_metrics(
    pipeline: Any,
    ctx: Any,
    w_prev: float | None,
    w_current: float | None,
) -> AdaptiveSnapshot | None:
    injected = adaptive_snapshot(ctx)
    if (
        injected is not None
        and getattr(injected, "is_available", False)
        and getattr(injected, "is_unstable", False)
    ):
        return injected

    metrics: AdaptiveSnapshot | None = None

    try:
        switching_ctx = scientific_of(ctx).switching
        switching_runtime = switching_ctx.switching_runtime
        switching_params = switching_ctx.switching_params
        if (
            w_prev is not None
            and w_current is not None
            and switching_runtime is not None
            and switching_params is not None
        ):
            if not hasattr(pipeline, "adaptive_observer"):
                pipeline.adaptive_observer = AdaptiveRuntimeObserver(
                    estimator=pipeline.adaptive_kappa_estimator
                )

            tau_d = float(switching_runtime.dwell_time())
            J = float(switching_params.J)

            metrics = pipeline.adaptive_observer.update(
                W_prev=w_prev,
                W_next=w_current,
                J=J,
                tau_d=tau_d,
            )

            set_adaptive_snapshot(ctx, metrics)

    except Exception as exc:
        metrics = None
        ErrorManager.capture_exception(
            ctx,
            exc,
            code="adaptive_metrics_compute_failure",
        )

    if metrics is None:
        metrics = adaptive_snapshot(ctx)

    return metrics


def apply_kappa_margin_layer(
    ctx: Any,
    pre_verdict: LyapunovVerdict,
    adaptive_metrics: AdaptiveSnapshot | None,
) -> None:
    try:
        if adaptive_metrics is None or adaptive_metrics.margin is None:
            return

        kappa_margin = float(adaptive_metrics.margin)

        ctx.extra["kappa_margin"] = kappa_margin

        # Single policy table (DM-H9): same thresholds as the control
        # stage, by construction.
        kappa_band = kappa_band_of(kappa_margin)

        if (journal := journal_of(ctx)) is not None:
            journal.kappa_band = kappa_band
        ctx.extra["kappa_band"] = kappa_band

        reasons = fusion_reasons_of(ctx)

        if kappa_band == "critical":
            if "kappa_margin_critical" not in reasons:
                reasons.append("kappa_margin_critical")

            if pre_verdict == LyapunovVerdict.ALLOW:
                if journal is not None:
                    journal.kappa_margin_forced_confirmation = True
                ctx.extra["_kappa_margin_forced_confirmation"] = True

        elif kappa_band == "warning":
            if "kappa_margin_warning" not in reasons:
                reasons.append("kappa_margin_warning")

    except Exception as exc:
        ErrorManager.capture_exception(
            ctx,
            exc,
            code="adaptive_kappa_margin_failure",
        )


def updated_pre_verdict(
    ctx: Any,
    pre_verdict: LyapunovVerdict,
    adaptive_metrics: AdaptiveSnapshot | None,
) -> LyapunovVerdict:
    # One-shot consume of the kappa-margin latch. The journal is the
    # storage (LOT O3); the export key is popped alongside so the
    # host-visible extra stays byte-identical. The pop result is still
    # honored on its own: a seeded forcing flag must keep forcing
    # (F-001, hardening-only), and partial duck contexts have no
    # journal at all.
    forced_export = bool(
        ctx.extra.pop(
            "_kappa_margin_forced_confirmation",
            False,
        )
    )
    forced = forced_export
    if (journal := journal_of(ctx)) is not None:
        forced = forced or journal.kappa_margin_forced_confirmation
        journal.kappa_margin_forced_confirmation = False
    if forced:
        return LyapunovVerdict.REQUIRE_CONFIRMATION

    if (
        adaptive_metrics is not None
        and getattr(adaptive_metrics, "is_available", False)
        and getattr(adaptive_metrics, "is_unstable", False)
    ):
        return LyapunovVerdict.ABSTAIN

    return pre_verdict


def apply_adaptive_unavailable_floor(
    ctx: Any,
    verdict: LyapunovVerdict,
    adaptive_metrics: AdaptiveSnapshot | None,
    w_prev: float | None,
    w_current: float | None,
) -> LyapunovVerdict:
    """Fail-closed floor for an adaptive layer that should be live.

    Campaign GATE-SEM (DM-G1, aligned with F-002): on a turn carrying
    both composite energies the adaptive layer is expected to produce
    a usable margin. If it did not (a genuine computation failure, or
    a degenerate near-zero previous energy), the missing measurement
    must constrain the verdict instead of silently constraining
    nothing: ALLOW floors to REQUIRE_CONFIRMATION. Unthreaded turns
    (no previous energy) are untouched; the layer is not expected
    there and the rest of the stack already floors them.
    """
    if w_prev is None or w_current is None:
        return verdict

    margin = (
        getattr(adaptive_metrics, "margin", None)
        if adaptive_metrics is not None
        else None
    )
    available = bool(
        adaptive_metrics is not None
        and getattr(adaptive_metrics, "is_available", False)
    )
    if available and margin is not None:
        return verdict

    reasons = fusion_reasons_of(ctx)
    if "adaptive_unavailable" not in reasons:
        reasons.append("adaptive_unavailable")

    if verdict == LyapunovVerdict.ALLOW:
        record_verdict_transition(
            ctx,
            stage="adaptive_unavailable_floor",
            before=verdict,
            after=LyapunovVerdict.REQUIRE_CONFIRMATION,
            reason="adaptive_unavailable",
        )
        return LyapunovVerdict.REQUIRE_CONFIRMATION
    return verdict


def apply_final_adaptive_veto(
    ctx: Any,
    verdict: LyapunovVerdict,
    adaptive_metrics: AdaptiveSnapshot | None,
) -> LyapunovVerdict:
    if (
        adaptive_metrics is not None
        and getattr(adaptive_metrics, "is_available", False)
        and getattr(adaptive_metrics, "is_unstable", False)
    ):
        if (journal := journal_of(ctx)) is not None:
            journal.hard_adaptive_veto = True
        ctx.extra["_hard_adaptive_veto"] = True
        # LOT G5: the veto flag is set regardless (the global-policy
        # relaxation guard consults it), but the trace records only a
        # real transition, never an ABSTAIN -> ABSTAIN no-op.
        if verdict != LyapunovVerdict.ABSTAIN:
            record_verdict_transition(
                ctx,
                stage="final_adaptive_hard_veto",
                before=verdict,
                after=LyapunovVerdict.ABSTAIN,
                reason="adaptive_metrics_unstable",
            )

        verdict = LyapunovVerdict.ABSTAIN

    return verdict


__all__ = [
    "AdaptiveRuntimeObserver",
    "compute_adaptive_metrics",
    "apply_kappa_margin_layer",
    "updated_pre_verdict",
    "apply_adaptive_unavailable_floor",
    "apply_final_adaptive_veto",
]
