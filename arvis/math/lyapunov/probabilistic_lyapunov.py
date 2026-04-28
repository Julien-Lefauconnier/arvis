# arvis/math/lyapunov/probabilistic_lyapunov.py

from collections import deque
from dataclasses import dataclass

from arvis.math.control.beta_adaptive import BetaAdaptiveController
from arvis.math.core.normalization import clamp01
from arvis.math.lyapunov.lyapunov import LyapunovState, V
from arvis.math.stability.regime_estimator import RegimeSnapshot


@dataclass(frozen=True)
class ProbLyapunovParams:
    window_size: int = 30
    warn_ucb: float = 0.6
    critical_ucb: float = 0.8


@dataclass(frozen=True)
class ProbLyapunovSnapshot:
    mean_v: float
    var_v: float
    std_v: float
    ucb_v: float
    beta: float
    window_size: int
    verdict: str


class ProbabilisticLyapunovObserver:
    """
    Probabilistic + adaptive Lyapunov observer.
    """

    def __init__(
        self,
        params: ProbLyapunovParams | None = None,
        beta_controller: BetaAdaptiveController | None = None,
    ):
        self.params = params or ProbLyapunovParams()
        self.beta_controller = beta_controller or BetaAdaptiveController()
        self._values: deque[float] = deque(maxlen=self.params.window_size)

    def push(
        self,
        state: LyapunovState,
        regime: RegimeSnapshot | None = None,
        drift: float = 0.0,
    ) -> ProbLyapunovSnapshot:
        v = clamp01(V(state))
        self._values.append(v)

        if len(self._values) < 2:
            return ProbLyapunovSnapshot(
                mean_v=v,
                var_v=0.0,
                std_v=0.0,
                ucb_v=v,
                beta=1.0,
                window_size=len(self._values),
                verdict="OK",
            )

        values = list(self._values)

        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / len(values)
        std = var**0.5

        beta = self.beta_controller.compute(
            regime=regime,
            variance=var,
            drift=drift,
        )

        ucb = clamp01(mean + beta * std)

        verdict = "OK"

        if ucb >= self.params.critical_ucb:
            verdict = "CRITICAL"
        elif ucb >= self.params.warn_ucb:
            verdict = "WARN"

        return ProbLyapunovSnapshot(
            mean_v=float(mean),
            var_v=float(var),
            std_v=float(std),
            ucb_v=float(ucb),
            beta=float(beta),
            window_size=len(values),
            verdict=verdict,
        )
