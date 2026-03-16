# arvis/cognition/retrieval/cognitive_retrieval_snapshot.py

from dataclasses import dataclass, field
from typing import List


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
    item_ids: List[str] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    semantic_roles: List[str] = field(default_factory=list)
    confidence: float = 0.0