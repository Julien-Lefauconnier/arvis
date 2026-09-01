# arvis/math/adaptive/adaptive_runtime_observer.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator

from .adaptive_snapshot import AdaptiveSnapshot


@dataclass
class AdaptiveRuntimeObserver:
    estimator: AdaptiveKappaEffEstimator

    def update(
        self,
        W_prev: float | None,
        W_next: float | None,
        J: float,
        tau_d: float,
    ) -> AdaptiveSnapshot:
        # -----------------------------------------
        # Guard: insufficient data
        # -----------------------------------------
        if W_prev is None or W_next is None or W_prev <= 0:
            return AdaptiveSnapshot(
                kappa_eff=None,
                margin=None,
                regime="critical",
                available=False,
            )

        snap = self.estimator.update(W_prev=W_prev, W_next=W_next)

        # Direct, typed reads (DM-B0): the estimator snapshot carries
        # kappa_raw/kappa_clipped/kappa_smoothed since MATH-A M4; a
        # getattr on the historical "kappa_eff" name silently returned
        # None and left this whole layer structurally dead on every
        # live path (only injected snapshots ever exercised the bands).
        kappa_eff: float | None = snap.kappa_smoothed
        margin: float | None = None

        if snap.is_available and kappa_eff is not None:
            margin = self.estimator.adaptive_switching_margin(
                J=J,
                tau_d=tau_d,
            )

        # -----------------------------------------
        # Regime classification
        # -----------------------------------------
        if margin is None:
            regime = "critical"
            available = False
        elif margin < 0:
            regime = "stable"
            available = True
        elif margin < 0.1:
            regime = "critical"
            available = True
        else:
            regime = "unstable"
            available = True

        return AdaptiveSnapshot(
            kappa_eff=kappa_eff,
            margin=margin,
            regime=regime,
            available=available,
        )
