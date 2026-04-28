# arvis/math/predictive/predictive_multi_horizon.py

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from arvis.math.core.normalization import clamp01
from arvis.math.lyapunov.lyapunov import LyapunovState, V, delta_V


@dataclass(frozen=True)
class MultiHorizonPredictiveParams:
    """
    Multi-horizon predictive stability parameters.

    - horizons: steps ahead for short/medium/long prediction
    - window_size: how many past steps to estimate slope
    - warn_pred_v / critical_pred_v: thresholds on predicted V (max over horizons)
    - warn_ttc / critical_ttc: thresholds on time-to-critical (steps)
    - ttc_target_v: V level defining "critical line" for TTC computation
    """

    horizons: tuple[int, int, int] = (5, 25, 100)
    window_size: int = 20

    warn_pred_v: float = 0.60
    critical_pred_v: float = 0.80

    warn_ttc: int = 15
    critical_ttc: int = 5

    ttc_target_v: float = 0.80


@dataclass(frozen=True)
class MultiHorizonPredictiveSnapshot:
    window_size: int
    horizons: tuple[int, int, int]
    last_v: float
    slope: float

    short_v: float
    medium_v: float
    long_v: float

    time_to_critical: int | None
    verdict: str

    # --- Compatibility with existing fusion code ---
    @property
    def predicted_v(self) -> float:
        # keep a single representative predicted_v (use long horizon)
        return float(self.long_v)

    @property
    def horizon(self) -> int:
        # representative horizon used by some code paths
        return int(self.horizons[-1])


class MultiHorizonPredictiveObserver:
    """
    Multi-horizon predictive observer (passive, no gating).

    Estime une pente sur V à partir des N derniers états,
    puis prédit V à plusieurs horizons (court / moyen / long).

    Objectifs:
    - mieux détecter drift lent (long horizon)
    - mieux détecter shocks (short horizon)
    - garder compat avec PredictiveSnapshot (predicted_v/horizon/window_size)
    """

    def __init__(self, params: MultiHorizonPredictiveParams | None = None):
        self.params = params or MultiHorizonPredictiveParams()
        self._states: deque[LyapunovState] = deque(maxlen=self.params.window_size)

    def reset(self) -> None:
        self._states.clear()

    def push(self, state: LyapunovState) -> MultiHorizonPredictiveSnapshot:
        self._states.append(state)

        last_v = clamp01(V(state))

        # not enough history => no slope
        if len(self._states) < 2:
            short_h, med_h, long_h = self.params.horizons
            return MultiHorizonPredictiveSnapshot(
                window_size=len(self._states),
                horizons=self.params.horizons,
                last_v=last_v,
                slope=0.0,
                short_v=last_v,
                medium_v=last_v,
                long_v=last_v,
                time_to_critical=None,
                verdict="OK",
            )

        # signed deltas over the window
        deltas: list[float] = [
            float(delta_V(self._states[i - 1], self._states[i]))
            for i in range(1, len(self._states))
        ]

        # slope estimate (mean signed delta)
        try:
            slope = sum(deltas) / max(1, len(deltas))
        except Exception:
            slope = 0.0

        short_h, med_h, long_h = self.params.horizons

        short_v = clamp01(last_v + slope * float(short_h))
        medium_v = clamp01(last_v + slope * float(med_h))
        long_v = clamp01(last_v + slope * float(long_h))

        # -------------------------------------------------
        # Slow drift amplifier (critical for adversarial drift)
        # -------------------------------------------------
        # A very slow slope must still become visible on long horizon.
        # This keeps system robust against poisoning and concept drift.
        if slope > 0.0:
            drift_amp = clamp01((slope * float(long_h)) ** 0.7 * 8.0)
            long_v = max(long_v, drift_amp)

        # time-to-critical only meaningful if slope > 0
        ttc: int | None = None
        if slope > 0.0:
            target = float(self.params.ttc_target_v)
            if last_v >= target:
                ttc = 0
            else:
                needed = (target - last_v) / slope
                if needed < 0:
                    ttc = 0
                else:
                    n = int(needed)
                    ttc = n if float(n) == needed else n + 1

        max_pred = max(short_v, medium_v, long_v)

        verdict = "OK"
        if max_pred >= self.params.critical_pred_v or (
            ttc is not None and ttc <= self.params.critical_ttc
        ):
            verdict = "CRITICAL"
        elif max_pred >= self.params.warn_pred_v or (
            ttc is not None and ttc <= self.params.warn_ttc
        ):
            verdict = "WARN"

        return MultiHorizonPredictiveSnapshot(
            window_size=len(self._states),
            horizons=self.params.horizons,
            last_v=float(last_v),
            slope=float(slope),
            short_v=float(short_v),
            medium_v=float(medium_v),
            long_v=float(long_v),
            time_to_critical=ttc,
            verdict=verdict,
        )
