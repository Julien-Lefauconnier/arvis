# arvis/math/signals/conflict.py

from dataclasses import dataclass


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass(frozen=True)
class ConflictSignal:
    global_score: float = 0.0
    epistemic: float = 0.0
    decisional: float = 0.0
    temporal: float = 0.0
    ethical: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "global_score", _clamp01(self.global_score))
        object.__setattr__(self, "epistemic", _clamp01(self.epistemic))
        object.__setattr__(self, "decisional", _clamp01(self.decisional))
        object.__setattr__(self, "temporal", _clamp01(self.temporal))
        object.__setattr__(self, "ethical", _clamp01(self.ethical))

    @classmethod
    def from_scalar(cls, value: float) -> "ConflictSignal":
        v = max(0.0, min(1.0, value))
        return cls(
            global_score=v,
            epistemic=0.0,
            decisional=v,
            temporal=0.0,
            ethical=0.0,
        )

    def clamp(self) -> "ConflictSignal":
        return ConflictSignal(
            global_score=_clamp01(self.global_score),
            epistemic=_clamp01(self.epistemic),
            decisional=_clamp01(self.decisional),
            temporal=_clamp01(self.temporal),
            ethical=_clamp01(self.ethical),
        )

    def __float__(self) -> float:
        return self.global_score

    # ------------------------------------------------------------
    # Helpers (expected by tests)
    # ------------------------------------------------------------

    def level(self) -> float:
        return self.global_score

    def is_zero(self) -> bool:
        return self.global_score == 0.0

    def is_max(self) -> bool:
        return self.global_score == 1.0
