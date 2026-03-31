# arvis/reflexive/timeline/insight/irg_timeline_insight.py

from dataclasses import dataclass
from typing import Sequence

from arvis.timeline.timeline_types import TimelineEntryType


@dataclass(frozen=True)
class IRGTimelineInsight:
    """
    Passive reflexive insight about a timeline view.

    - Read-only
    - Declarative
    - Non-prescriptive
    - ZKCS compliant

    An insight NEVER grants or denies access.
    """

    view_role: str
    dominant_entry_types: Sequence[TimelineEntryType]
    confidence: float            # 0.0 → 1.0
    message: str                 # human-readable, non-sensitive
