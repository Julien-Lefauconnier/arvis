# arvis/reflexive/explanation/timeline/irg_timeline_explanation.py

from collections.abc import Sequence
from dataclasses import dataclass


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
    stability: str | None = None
