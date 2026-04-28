# arvis/math/signals/system_tension.py

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemTensionSignal:
    """
    Unified system tension signal.

    Combines:
    - collapse risk (physical instability)
    - drift (dynamic instability)
    - conflict pressure (cognitive instability)

    Kernel-level signal.
    """

    collapse: float
    drift: float
    conflict: float

    def level(self) -> float:
        return max(self.collapse, self.drift, self.conflict)

    def is_high(self, threshold: float = 0.7) -> bool:
        return self.level() > threshold

    def dominant_axis(self) -> str:
        m = self.level()
        if m == self.collapse:
            return "collapse"
        if m == self.drift:
            return "drift"
        return "conflict"
