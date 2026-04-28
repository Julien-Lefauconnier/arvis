# arvis/cognition/knowledge/knowledge_event.py

from dataclasses import dataclass
from datetime import datetime

from .knowledge_snapshot import KnowledgeSnapshot


@dataclass(frozen=True)
class KnowledgeEvent:
    """
    Declarative knowledge event.

    Kernel invariants:
    - immutable
    - no side effects
    - no internal generation
    """

    event_id: str
    snapshot: KnowledgeSnapshot
    user_id: str | None
    place_id: str | None
    created_at: datetime
