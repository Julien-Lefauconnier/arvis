# arvis/knowledge/knowledge_snapshot.py

from dataclasses import dataclass, field
from datetime import UTC, datetime

from arvis.knowledge.knowledge_signal import KnowledgeSignal
from arvis.knowledge.knowledge_state import KnowledgeState


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """
    Immutable, declarative snapshot of Veramem's epistemic state
    at a given moment in time.
    """

    state: KnowledgeState
    signals: list[KnowledgeSignal]
    scope: str | None = None

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
