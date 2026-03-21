# arvis/math/state/fast_state.py

from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class FastCognitiveState:
    """
    Internal fast state (theoretical x_t).
    Not directly used for gating yet.
    """

    values: Tuple[float, ...]

    def dim(self) -> int:
        return len(self.values)