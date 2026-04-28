# arvis/math/switching/regime_state.py

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TheoreticalRegime(StrEnum):
    STABLE = "stable"
    OSCILLATORY = "oscillatory"
    CRITICAL = "critical"
    CHAOTIC = "chaotic"
    TRANSITION = "transition"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class RegimeState:
    q_t: TheoreticalRegime
    confidence: float = 0.0
