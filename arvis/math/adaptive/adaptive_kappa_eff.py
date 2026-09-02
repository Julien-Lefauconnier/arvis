# arvis/math/adaptive/adaptive_kappa_eff.py
"""Empirical contraction-factor estimation.

Naming, precisely (audit M6/M7 disambiguation, campaign MATH-A M4):
the quantity estimated here is the EMPIRICAL CONTRACTION FACTOR
``kappa = 1 - W_next / W_prev`` of the observed energy sequence (the
per-step geometric decrease; ``W_next <= (1 - kappa) * W_prev``). It is
NOT the theoretical small-gain margin ``kappa_eff = alpha - gamma_z *
eta * L_T`` of assumption A12 (``docs/math/M1_assumptions.md``), which
is a statement about Lipschitz constants nobody measures at runtime.
The two used to share one name; they are different objects and this
module estimates only the empirical one.

Divergence handling (audit G5): a raw factor is clipped to
``[kappa_min, kappa_max]`` with ``kappa_min = -1.0``, so an energy
blow-up dents the smoothed estimate instead of being erased (the old
floor of 0.0 made a x100 divergence indistinguishable from a neutral
step). Independently of smoothing, consecutive divergences are counted:
one divergence downgrades the regime to at most "marginal", and a
streak of ``divergence_streak_limit`` forces "unstable" regardless of
how healthy the smoothed history still looks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from arvis.math.switching.switching_params import DWELL_TIME_FLOOR


@dataclass(frozen=True)
class AdaptiveKappaConfig:
    epsilon: float = 1e-8
    smoothing: float = 0.2
    # Reporting floor for a single step: -1.0 keeps a doubling (or
    # worse) visible to the smoother instead of erasing it (G5).
    kappa_min: float = -1.0
    kappa_max: float = 0.95
    unstable_threshold: float = 0.0
    marginal_threshold: float = 0.05
    # Consecutive divergences (raw kappa < 0) that force "unstable"
    # regardless of the smoothed value.
    divergence_streak_limit: int = 3


@dataclass(frozen=True)
class AdaptiveKappaSnapshot:
    kappa_raw: float | None
    kappa_clipped: float | None
    kappa_smoothed: float | None
    is_available: bool
    regime: str
    divergence_streak: int = 0


class AdaptiveKappaEffEstimator:
    """Estimator of the empirical contraction factor (see module doc).

    The class name keeps its historical ``KappaEff`` for compatibility;
    the estimated quantity is the empirical factor, not A12's
    ``kappa_eff``.
    """

    def __init__(self, config: AdaptiveKappaConfig | None = None) -> None:
        self._config = config or AdaptiveKappaConfig()
        self._kappa_smoothed: float | None = None
        self._divergence_streak = 0

    @property
    def config(self) -> AdaptiveKappaConfig:
        return self._config

    @property
    def kappa_smoothed(self) -> float | None:
        return self._kappa_smoothed

    @property
    def divergence_streak(self) -> int:
        return self._divergence_streak

    def update(self, W_prev: float, W_next: float) -> AdaptiveKappaSnapshot:
        if W_prev <= self._config.epsilon:
            return AdaptiveKappaSnapshot(
                kappa_raw=None,
                kappa_clipped=None,
                kappa_smoothed=self._kappa_smoothed,
                is_available=False,
                regime="unavailable",
                divergence_streak=self._divergence_streak,
            )

        kappa_raw = 1.0 - (float(W_next) / float(W_prev))

        # Divergence accounting happens on the RAW value, before any
        # clipping or smoothing can soften it (G5).
        if kappa_raw < 0.0:
            self._divergence_streak += 1
        else:
            self._divergence_streak = 0

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

        regime = self._regime(self._kappa_smoothed, self._divergence_streak)

        return AdaptiveKappaSnapshot(
            kappa_raw=kappa_raw,
            kappa_clipped=kappa_clipped,
            kappa_smoothed=self._kappa_smoothed,
            is_available=True,
            regime=regime,
            divergence_streak=self._divergence_streak,
        )

    def _regime(self, smoothed: float, streak: int) -> str:
        cfg = self._config
        if streak >= cfg.divergence_streak_limit or smoothed <= cfg.unstable_threshold:
            return "unstable"
        if streak >= 1 or smoothed <= cfg.marginal_threshold:
            # A single observed divergence caps the regime at
            # "marginal": the smoothed history may still look healthy,
            # but "stable" must not describe a step where the energy
            # grew (G5).
            return "marginal"
        return "stable"

    def adaptive_switching_margin(self, J: float, tau_d: float) -> float | None:
        """T1-shaped margin ``ln(J)/tau_d + ln(1 - kappa_smoothed)``.

        A non-positive dwell is floored to ``DWELL_TIME_FLOOR``, the
        same floor ``switching_lhs`` applies (campaign GATE-SEM,
        DM-G1): an empty dwell clock makes the margin massively
        positive, which is the veto the theory prescribes. The
        previous ``ValueError`` on ``tau_d <= 0`` was swallowed by the
        gate stage into ``metrics = None``, and an absent adaptive
        layer constrained nothing, so the least-guarded turn of every
        trajectory (the first threaded one) was the easiest to ALLOW:
        6 of 11 D-1.0 and 3 of 4 D-2.0 final ALLOW sat on that hole.
        """
        if self._kappa_smoothed is None:
            return None
        if J <= 0.0:
            raise ValueError("J must be strictly positive.")
        if self._kappa_smoothed >= 1.0:
            raise ValueError("smoothed contraction factor must stay below 1.")
        floored_tau_d = max(float(tau_d), DWELL_TIME_FLOOR)
        return (math.log(J) / floored_tau_d) + math.log(1.0 - self._kappa_smoothed)
