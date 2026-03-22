# arvis/math/adaptive/adaptive_runtime_observer.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator


@dataclass
class AdaptiveRuntimeObserver:
    estimator: AdaptiveKappaEffEstimator

    def update(
        self,
        W_prev: float,
        W_next: float,
        J: float,
        tau_d: float,
    ) -> Dict[str, Any]:
        snap = self.estimator.update(W_prev=W_prev, W_next=W_next)

        margin = None
        if snap.is_available:
            margin = self.estimator.adaptive_switching_margin(J=J, tau_d=tau_d)

        return {
            "kappa_eff": snap.kappa_smoothed,
            "margin": margin,
            "regime": snap.regime,
            "available": snap.is_available,
        }