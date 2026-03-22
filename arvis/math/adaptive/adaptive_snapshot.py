# arvis/math/adaptive/adaptive_snapshot.py

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AdaptiveSnapshot:
    """
    Canonical adaptive stability snapshot shared across pipeline.

    This replaces all dict-based adaptive payloads.
    """

    kappa_eff: Optional[float]
    margin: Optional[float]
    regime: str  # "stable", "critical", "unstable", "unavailable"
    available: bool

    @property
    def is_available(self) -> bool:
        return self.available and self.kappa_eff is not None

    @property
    def is_stable(self) -> bool:
        return self.is_available and self.margin is not None and self.margin < 0

    @property
    def is_unstable(self) -> bool:
        return self.is_available and self.margin is not None and self.margin >= 0