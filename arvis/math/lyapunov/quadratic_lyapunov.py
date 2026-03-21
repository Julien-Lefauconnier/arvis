# arvis/math/lyapunov/quadratic_lyapunov.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass(frozen=True)
class QuadraticLyapunovState:
    """
    Theoretical fast state x_t used for paper-aligned quadratic Lyapunov analysis.
    """
    x: np.ndarray

    def as_vector(self) -> np.ndarray:
        return np.asarray(self.x, dtype=float)


@dataclass(frozen=True)
class QuadraticLyapunovSnapshot:
    regime: str
    value: float
    delta: Optional[float]
    dimension: int

@dataclass(frozen=True)
class QuadraticComparabilitySnapshot:
    m: float
    M: float
    J: float
    regimes: int

class QuadraticLyapunovFamily:
    """
    Regime-dependent quadratic Lyapunov family:
        V_q(x) = x^T P_q x
    """

    def __init__(self, matrices: Dict[str, np.ndarray]):
        self._matrices = {
            str(k): np.asarray(v, dtype=float)
            for k, v in matrices.items()
        }

    def has_regime(self, regime: str) -> bool:
        return str(regime) in self._matrices

    def matrix(self, regime: str) -> np.ndarray:
        return self._matrices[str(regime)]

    def value(self, regime: str, state: QuadraticLyapunovState) -> float:
        x = state.as_vector()
        P = self.matrix(regime)
        return float(x.T @ P @ x)

    def delta(
        self,
        regime: str,
        prev_state: QuadraticLyapunovState,
        cur_state: QuadraticLyapunovState,
    ) -> float:
        return self.value(regime, cur_state) - self.value(regime, prev_state)
    
    def comparability(self) -> QuadraticComparabilitySnapshot:
        """
        Computes regime comparability constants:
            m = min_q λ_min(P_q)
            M = max_q λ_max(P_q)
            J = M / m
        """
        mins = []
        maxs = []

        for P in self._matrices.values():
            eigvals = np.linalg.eigvalsh(P)
            mins.append(float(np.min(eigvals)))
            maxs.append(float(np.max(eigvals)))

        m = max(min(mins), 1e-9)
        M = max(max(maxs), m)
        J = M / m

        return QuadraticComparabilitySnapshot(
            m=m,
            M=M,
            J=J,
            regimes=len(self._matrices),
        )


def make_default_quadratic_family(dim: int = 4) -> QuadraticLyapunovFamily:
    """
    Minimal paper-aligned default family.
    Positive definite diagonal matrices by regime.
    """
    identity = np.eye(dim, dtype=float)

    return QuadraticLyapunovFamily(
        matrices={
            "stable": 0.8 * identity,
            "oscillatory": 1.0 * identity,
            "critical": 1.2 * identity,
            "chaotic": 1.5 * identity,
            "transition": 1.0 * identity,
            "neutral": 1.0 * identity,
        }
    )