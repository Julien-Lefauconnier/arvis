# tests/kernel/gate/test_adaptive_fail_closed.py
"""The adaptive layer fails closed instead of silently disappearing.

Campaign GATE-SEM (LOT G1, audit P0-1, 2026-09-02). The mechanism the
campaign closes: ``adaptive_switching_margin`` raised ``ValueError``
on ``tau_d <= 0``, the gate stage swallowed the exception into
``metrics = None``, and every downstream veto checked
``is_available`` and did nothing. Unknown adaptive state constrained
nothing (fail-open), the exact opposite of the F-002 doctrine the
switching axis applies. Measured on the pre-campaign base: 8 of 13
D-1.0 and 13 of 15 D-2.0 final ALLOW were issued on turns where the
switching condition was violated by six orders of magnitude and the
adaptive layer was silently absent.

Pinned here:

1. The runtime observer produces a live, vetoing snapshot on an empty
   dwell clock instead of raising.
2. The gate stage computes usable metrics at ``tau_d = 0``.
3. A turn carrying both composite energies but no usable adaptive
   margin can not ALLOW (the fail-closed floor).
"""

from __future__ import annotations

from arvis.kernel.pipeline.stages.gate.adaptive import (
    apply_adaptive_unavailable_floor,
    compute_adaptive_metrics,
)
from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator
from arvis.math.adaptive.adaptive_runtime_observer import (
    AdaptiveRuntimeObserver,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.switching.switching_params import SwitchingParams
from arvis.math.switching.switching_runtime import SwitchingRuntime
from tests.fixtures.builders.context_builder import build_test_context

_PARAMS = SwitchingParams(alpha=0.15, gamma_z=0.4, eta=0.05, L_T=1.0, J=1.875)


def test_observer_vetoes_on_an_empty_dwell_clock() -> None:
    """RED on the pre-campaign tree: this call raised ValueError."""
    observer = AdaptiveRuntimeObserver(estimator=AdaptiveKappaEffEstimator())

    snap = observer.update(W_prev=1.0, W_next=0.9, J=1.875, tau_d=0.0)

    assert snap.is_available
    assert snap.margin is not None and snap.margin > 0.0
    assert snap.is_unstable
    assert snap.regime == "unstable"


class _Pipeline:
    adaptive_kappa_estimator = None

    def __init__(self) -> None:
        self.adaptive_kappa_estimator = AdaptiveKappaEffEstimator()


def test_gate_stage_metrics_are_live_at_zero_dwell() -> None:
    """RED on the pre-campaign tree: metrics came back None and the
    captured error was the only witness."""
    ctx = build_test_context()
    ctx.scientific.switching.switching_runtime = SwitchingRuntime()
    ctx.scientific.switching.switching_params = _PARAMS

    metrics = compute_adaptive_metrics(
        pipeline=_Pipeline(),
        ctx=ctx,
        w_prev=1.0,
        w_current=0.9,
    )

    assert metrics is not None
    assert metrics.is_available
    assert metrics.margin is not None and metrics.margin > 0.0
    assert metrics.is_unstable


def test_unavailable_layer_floors_allow_on_a_threaded_turn() -> None:
    ctx = build_test_context()

    verdict = apply_adaptive_unavailable_floor(
        ctx,
        LyapunovVerdict.ALLOW,
        adaptive_metrics=None,
        w_prev=1.0,
        w_current=0.9,
    )

    assert verdict is LyapunovVerdict.REQUIRE_CONFIRMATION
    assert "adaptive_unavailable" in ctx.journal.fusion_reasons
    entries = [
        e
        for e in ctx.journal.verdict_transition_trace
        if e["stage"] == "adaptive_unavailable_floor"
    ]
    assert len(entries) == 1


def test_unavailable_layer_leaves_unthreaded_turns_alone() -> None:
    ctx = build_test_context()

    verdict = apply_adaptive_unavailable_floor(
        ctx,
        LyapunovVerdict.ALLOW,
        adaptive_metrics=None,
        w_prev=None,
        w_current=0.9,
    )

    assert verdict is LyapunovVerdict.ALLOW
    assert "adaptive_unavailable" not in ctx.journal.fusion_reasons


def test_live_layer_passes_through_the_floor() -> None:
    ctx = build_test_context()
    observer = AdaptiveRuntimeObserver(estimator=AdaptiveKappaEffEstimator())
    live = observer.update(W_prev=1.0, W_next=0.9, J=1.875, tau_d=20.0)
    assert live.is_available and live.margin is not None

    verdict = apply_adaptive_unavailable_floor(
        ctx,
        LyapunovVerdict.ALLOW,
        adaptive_metrics=live,
        w_prev=1.0,
        w_current=0.9,
    )

    assert verdict is LyapunovVerdict.ALLOW
    assert "adaptive_unavailable" not in ctx.journal.fusion_reasons
