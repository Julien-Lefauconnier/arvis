# arvis/math/predicitive/predictive_stability.py

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional

from arvis.math.lyapunov.lyapunov import LyapunovState, V, delta_V
from arvis.math.core.normalization import clamp01


@dataclass(frozen=True)
class PredictiveStabilityParams:
    """
    Predictive stability parameters.

    - horizon: how many steps ahead to predict
    - window_size: how many past steps to use to estimate slope
    - warn_pred_v / critical_pred_v: thresholds on predicted V
    - warn_ttc / critical_ttc: thresholds on time-to-critical (in steps)
      If slope>0 and ttc <= threshold => WARN/CRITICAL (even if pred_v not huge yet)
    """
    horizon: int = 10
    window_size: int = 10

    warn_pred_v: float = 0.55
    critical_pred_v: float = 0.75

    warn_ttc: int = 10
    critical_ttc: int = 3

    # target critical line for ttc computation
    ttc_target_v: float = 0.75


@dataclass(frozen=True)
class PredictiveSnapshot:
    window_size: int
    horizon: int
    last_v: float
    slope: float
    predicted_v: float
    time_to_critical: Optional[int]
    verdict: str


class PredictiveStabilityObserver:
    """
    Short-horizon predictive observer (passive, no gating).

    It uses the last N LyapunovStates to estimate a slope on V,
    then predicts V at +horizon.

    Notes:
    - Uses signed mean(delta_V) as slope estimate (simple + robust enough for v1)
    - Everything clamped into [0,1] for exposed metrics
    """

    def __init__(self, params: PredictiveStabilityParams | None = None):
        self.params = params or PredictiveStabilityParams()
        # Store only V-values (ZKCS-safe numeric summaries).
        # Keeping LyapunovState in the public signature for compatibility.
        self._values: Deque[float] = deque(maxlen=self.params.window_size)

    def push(self, state: LyapunovState) -> PredictiveSnapshot:
        v = clamp01(V(state))
        return self.push_value(v)
    
    def push_value(self, v: float) -> PredictiveSnapshot:
        """
        Push a precomputed stability value V in [0,1].

        This enables hybrid stability projection (numeric+symbolic)
        without requiring a LyapunovState.
        """
        last_v = clamp01(float(v))
        self._values.append(last_v)

        # not enough history => no slope
        if len(self._values) < 2:
            return PredictiveSnapshot(
                window_size=len(self._values),
                horizon=self.params.horizon,
                last_v=last_v,
                slope=0.0,
                predicted_v=last_v,
                time_to_critical=None,
                verdict="OK",
            )

        # signed deltas over the window
        deltas: List[float] = []
        try:
            for i in range(1, len(self._values)):
                deltas.append(float(self._values[i] - self._values[i - 1]))
        except Exception:
            deltas = []

        # slope estimate (mean signed delta)
        slope = 0.0
        try:
            slope = sum(deltas) / max(1, len(deltas))
        except Exception:
            slope = 0.0

        # prediction
        predicted_v = clamp01(last_v + slope * float(self.params.horizon))

        # time-to-critical (steps), only meaningful if slope > 0
        ttc: Optional[int] = None
        if slope > 0.0:
            target = float(self.params.ttc_target_v)
            # if already beyond, ttc = 0
            if last_v >= target:
                ttc = 0
            else:
                # steps needed to reach target: ceil((target-last_v)/slope)
                needed = (target - last_v) / slope
                # protect numeric weirdness
                if needed < 0:
                    ttc = 0
                else:
                    # ceil without math import
                    n = int(needed)
                    ttc = n if float(n) == needed else n + 1

        verdict = "OK"

        # CRITICAL if predicted too high OR time-to-critical very small
        if predicted_v >= self.params.critical_pred_v or (ttc is not None and ttc <= self.params.critical_ttc):
            verdict = "CRITICAL"
        # WARN if predicted medium OR time-to-critical small-ish
        elif predicted_v >= self.params.warn_pred_v or (ttc is not None and ttc <= self.params.warn_ttc):
            verdict = "WARN"

        return PredictiveSnapshot(
            window_size=len(self._values),
            horizon=self.params.horizon,
            last_v=last_v,
            slope=float(slope),
            predicted_v=float(predicted_v),
            time_to_critical=ttc,
            verdict=verdict,
        )