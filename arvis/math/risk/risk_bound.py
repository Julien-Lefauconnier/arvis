# arvis/math/risk/risk_bound.py

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import log, sqrt
from typing import Deque, Optional


@dataclass(frozen=True)
class RiskBoundParams:
    window_size: int = 200
    delta: float = 0.01  # confidence level (1-delta)
    warn_p_ucb: float = 0.10
    critical_p_ucb: float = 0.25


@dataclass(frozen=True)
class RiskBoundSnapshot:
    n: int
    violations: int
    p_hat: float
    p_ucb: float
    verdict: str


class HoeffdingRiskBound:
    """
    PAC-style risk estimator on a sliding window.

    We track violation events (0/1), estimate empirical risk p_hat,
    and compute an upper confidence bound p_ucb via Hoeffding:

        p_ucb = min(1, p_hat + sqrt(log(1/delta)/(2n)))

    Deterministic, audit-friendly, ZKCS-compliant.
    """

    def __init__(self, params: Optional[RiskBoundParams] = None):
        self.params = params or RiskBoundParams()
        if not (0.0 < self.params.delta < 1.0):
            raise ValueError("delta must be in (0,1)")
        self._events: Deque[int] = deque(maxlen=self.params.window_size)

    def push(self, violation: bool) -> RiskBoundSnapshot:
        self._events.append(1 if violation else 0)

        n = len(self._events)
        v = sum(self._events)

        if n == 0:
            return RiskBoundSnapshot(
                n=0, violations=0, p_hat=0.0, p_ucb=0.0, verdict="OK"
            )

        p_hat = v / n
        eps = sqrt(log(1.0 / self.params.delta) / (2.0 * n))
        p_ucb = min(1.0, p_hat + eps)

        verdict = "OK"
        if p_ucb >= self.params.critical_p_ucb:
            verdict = "CRITICAL"
        elif p_ucb >= self.params.warn_p_ucb:
            verdict = "WARN"

        return RiskBoundSnapshot(
            n=n,
            violations=v,
            p_hat=float(p_hat),
            p_ucb=float(p_ucb),
            verdict=verdict,
        )
