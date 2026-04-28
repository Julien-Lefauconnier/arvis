# arvis/knowledge/knowledge_snapshot.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from datetime import timezone

from arvis.knowledge.knowledge_state import KnowledgeState
from arvis.knowledge.knowledge_signal import KnowledgeSignal


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """
    Immutable, declarative snapshot of Veramem's epistemic state
    at a given moment in time.
    """

    state: KnowledgeState
    signals: List[KnowledgeSignal]
    scope: Optional[str] = None

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
