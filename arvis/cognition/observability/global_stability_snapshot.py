# arvis/cognition/observability/global_stability_snapshot.py

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class GlobalStabilitySnapshot:
    verdict: str
    score: float
    confidence: float
    samples: int

    mean_dv: float
    std_dv: float
    instability_rate: float

    collapse_risk: float
    last_v: float

    reasons: List[str]