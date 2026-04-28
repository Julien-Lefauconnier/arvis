# arvis/cognition/retrieval/cognitive_retrieval_snapshot.py

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CognitiveRetrievalSnapshot:
    """
    ZKCS-safe retrieval snapshot.

    Contains:
    - no raw user data
    - no document text
    - no summaries
    - no reconstruction capability
    """

    source: str
    item_ids: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    semantic_roles: list[str] = field(default_factory=list)
    confidence: float = 0.0
