# arvis/cognition/knowledge/knowledge_event.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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
    user_id: Optional[str]
    place_id: Optional[str]
    created_at: datetime