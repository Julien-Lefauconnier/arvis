# arvis/cognition/bundle/cognitive_bundle_snapshot.py

from dataclasses import dataclass, field
from typing import Optional, Sequence, Dict, Any
from datetime import datetime, timezone

from arvis.cognition.decision.decision_result import DecisionResult
from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot
from arvis.cognition.retrieval.cognitive_retrieval_snapshot import (
    CognitiveRetrievalSnapshot,
)

from arvis.timeline.timeline_entry import TimelineEntry
from arvis.memory.memory_long_snapshot import MemoryLongSnapshot


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class CognitiveBundleSnapshot:
    """
    Frozen and exposable view of the current cognitive state.

    Kernel guarantees:
    - non executable
    - non prescriptive
    - zero-knowledge native
    """

    decision_result: DecisionResult
    introspection: IntrospectionSnapshot
    explanation: ExplanationSnapshot
    timeline: Sequence[TimelineEntry]

    memory_long: Optional[MemoryLongSnapshot] = None
    retrieval_snapshot: Optional[CognitiveRetrievalSnapshot] = None

    generated_at: datetime = field(default_factory=utcnow)

    # Declarative context hints (MemoryLong-driven)
    context_hints: Dict[str, Any] = field(default_factory=dict)