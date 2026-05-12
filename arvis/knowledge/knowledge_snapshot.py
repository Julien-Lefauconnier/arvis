# arvis/knowledge/knowledge_snapshot.py

from dataclasses import dataclass, field
from datetime import datetime

from arvis.knowledge.knowledge_signal import KnowledgeSignal
from arvis.knowledge.knowledge_state import KnowledgeState
from arvis.types.timestamps import utcnow


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """
    Immutable, declarative snapshot of system epistemic state
    at a given moment in time.
    """

    state: KnowledgeState
    signals: list[KnowledgeSignal]
    scope: str | None = None

    created_at: datetime = field(default_factory=utcnow)
