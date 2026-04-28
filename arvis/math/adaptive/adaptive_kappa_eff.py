# arvis/math/adaptive/adaptive_kappa_eff.py

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveKappaConfig:
    epsilon: float = 1e-8
    smoothing: float = 0.2
    kappa_min: float = 0.0
    kappa_max: float = 0.95
    unstable_threshold: float = 0.0
    marginal_threshold: float = 0.05


@dataclass(frozen=True)
class AdaptiveKappaSnapshot:
    kappa_raw: float | None
    kappa_clipped: float | None
    kappa_smoothed: float | None
    is_available: bool
    regime: str


class AdaptiveKappaEffEstimator:
    def __init__(self, config: AdaptiveKappaConfig | None = None) -> None:
        self._config = config or AdaptiveKappaConfig()
        self._kappa_smoothed: float | None = None

    @property
    def config(self) -> AdaptiveKappaConfig:
        return self._config

    @property
    def kappa_smoothed(self) -> float | None:
        return self._kappa_smoothed

    def update(self, W_prev: float, W_next: float) -> AdaptiveKappaSnapshot:
        if W_prev <= self._config.epsilon:
            return AdaptiveKappaSnapshot(
                kappa_raw=None,
                kappa_clipped=None,
                kappa_smoothed=self._kappa_smoothed,
                is_available=False,
                regime="unavailable",
            )

        kappa_raw = 1.0 - (float(W_next) / float(W_prev))
        kappa_clipped = min(
            self._config.kappa_max,
            max(self._config.kappa_min, kappa_raw),
        )

        if self._kappa_smoothed is None:
            self._kappa_smoothed = kappa_clipped
        else:
            rho = self._config.smoothing
            self._kappa_smoothed = (
                1.0 - rho
            ) * self._kappa_smoothed + rho * kappa_clipped

        if self._kappa_smoothed <= self._config.unstable_threshold:
            regime = "unstable"
        elif self._kappa_smoothed <= self._config.marginal_threshold:
            regime = "marginal"
        else:
            regime = "stable"

        return AdaptiveKappaSnapshot(
            kappa_raw=kappa_raw,
            kappa_clipped=kappa_clipped,
            kappa_smoothed=self._kappa_smoothed,
            is_available=True,
            regime=regime,
        )

    def adaptive_switching_margin(self, J: float, tau_d: float) -> float | None:
        if self._kappa_smoothed is None:
            return None
        if J <= 0.0 or tau_d <= 0.0:
            raise ValueError("J and tau_d must be strictly positive.")
        return (math.log(J) / tau_d) + math.log(1.0 - self._kappa_smoothed)
