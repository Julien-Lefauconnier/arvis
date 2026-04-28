# arvis/math/core/fast_dynamics.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True)
class FastDynamicsSnapshot:
    """
    Paper-aligned fast dynamics:
        x_{t+1} = f_q(x_t, z_t, w_t)
    """

    regime: Optional[str]
    x_prev: Optional[Any]
    x_next: Optional[Any]
    delta_norm: Optional[float]

    def is_valid(self) -> bool:
        return self.x_prev is not None and self.x_next is not None
