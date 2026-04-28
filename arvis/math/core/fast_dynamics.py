# arvis/math/core/fast_dynamics.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FastDynamicsSnapshot:
    """
    Paper-aligned fast dynamics:
        x_{t+1} = f_q(x_t, z_t, w_t)
    """

    regime: str | None
    x_prev: Any | None
    x_next: Any | None
    delta_norm: float | None

    def is_valid(self) -> bool:
        return self.x_prev is not None and self.x_next is not None
