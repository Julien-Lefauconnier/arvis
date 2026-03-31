# arvis/reflexive/explanation/timeline/irg_timeline_explanation.py

from dataclasses import dataclass
from typing import Sequence, Optional


@dataclass(frozen=True)
class IRGTimelineExplanation:
    """
    Human-readable explanation derived from reflexive
    timeline observations.

    Characteristics:
    - Declarative
    - Non prescriptive
    - Non authoritative
    """

    summary: str
    signals: Sequence[str]
    stability: Optional[str] = None
