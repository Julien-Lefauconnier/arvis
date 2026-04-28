# arvis/math/predictive/trajectory_observer.py

from collections import deque
from dataclasses import dataclass

from arvis.math.core.normalization import clamp01
from arvis.math.lyapunov.lyapunov import LyapunovState, V, delta_V


@dataclass
class TrajectoryParams:
    window_size: int = 20

    warn_vmax: float = 0.6
    critical_vmax: float = 0.8

    warn_drift_sum: float = 0.5
    critical_drift_sum: float = 1.0


@dataclass
class TrajectorySnapshot:
    window_size: int
    last_v: float
    v_max: float
    drift_pos_sum: float
    mean_abs_delta: float
    verdict: str


class TrajectoryObserver:
    """
    Multi-horizon stability observer.

    Passive:
    - no gating
    - no control
    """

    def __init__(self, params: TrajectoryParams | None = None):
        self.params = params or TrajectoryParams()
        self._states: deque[LyapunovState] = deque(maxlen=self.params.window_size)

    def push(self, state: LyapunovState) -> TrajectorySnapshot:
        self._states.append(state)

        if len(self._states) == 1:
            v = V(state)
            return TrajectorySnapshot(
                window_size=1,
                last_v=v,
                v_max=v,
                drift_pos_sum=0.0,
                mean_abs_delta=0.0,
                verdict="OK",
            )

        vs = [V(s) for s in self._states]
        v_max = clamp01(max(vs))

        deltas = [
            abs(delta_V(self._states[i - 1], self._states[i]))
            for i in range(1, len(self._states))
        ]

        drift_pos = [
            max(0.0, delta_V(self._states[i - 1], self._states[i]))
            for i in range(1, len(self._states))
        ]

        # Normalized metrics
        drift_mean = clamp01(sum(drift_pos) / len(drift_pos))
        mean_delta = clamp01(sum(deltas) / len(deltas))
        shock = clamp01(max(deltas))

        verdict = "OK"

        if (
            v_max >= self.params.critical_vmax
            or shock >= self.params.critical_drift_sum
        ):
            verdict = "CRITICAL"
        elif v_max >= self.params.warn_vmax or drift_mean >= self.params.warn_drift_sum:
            verdict = "WARN"

        return TrajectorySnapshot(
            window_size=len(self._states),
            last_v=vs[-1],
            v_max=v_max,
            drift_pos_sum=drift_mean,
            mean_abs_delta=mean_delta,
            verdict=verdict,
        )
