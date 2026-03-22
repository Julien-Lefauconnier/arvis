# arvis/math/adaptive/adaptive_runtime_observer.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator
from .adaptive_snapshot import AdaptiveSnapshot


@dataclass
class AdaptiveRuntimeObserver:
    estimator: AdaptiveKappaEffEstimator

    def update(
        self,
        W_prev: Optional[float],
        W_next: Optional[float],
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

        kappa_eff: Optional[float] = getattr(snap, "kappa_eff", None)
        margin: Optional[float] = None

        if getattr(snap, "is_available", False) and kappa_eff is not None:
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