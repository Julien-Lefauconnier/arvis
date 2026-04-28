# arvis/cognition/bundle/cognitive_bundle_snapshot.py

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from arvis.cognition.decision.decision_result import DecisionResult
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot
from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.cognition.retrieval.cognitive_retrieval_snapshot import (
    CognitiveRetrievalSnapshot,
)
from arvis.memory.memory_long_snapshot import MemoryLongSnapshot
from arvis.timeline.timeline_entry import TimelineEntry


def utcnow() -> datetime:
    return datetime.now(UTC)


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

    memory_long: MemoryLongSnapshot | None = None
    retrieval_snapshot: CognitiveRetrievalSnapshot | None = None

    generated_at: datetime = field(default_factory=utcnow)

    # -----------------------------------------------------
    # Derived memory influence (ZKCS-safe)
    # -----------------------------------------------------
    memory_features: dict[str, Any] = field(default_factory=dict)

    # Declarative context hints (MemoryLong-driven)
    context_hints: dict[str, Any] = field(default_factory=dict)
