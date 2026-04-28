# arvis/kernel_core/process/priority.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CognitivePriority:
    value: float

    def normalized(self) -> float:
        if self.value < 0.0:
            return 0.0
        if self.value > 100.0:
            return 100.0
        return float(self.value)
