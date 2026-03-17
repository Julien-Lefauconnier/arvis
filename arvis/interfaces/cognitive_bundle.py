# arvis/interfaces/cognitive_bundle.py

from typing import Protocol, Sequence, Dict, Any, Optional
from datetime import datetime

from arvis.cognition.decision.decision_result import DecisionResult
from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot


class CognitiveBundle(Protocol):
    """
    Canonical cognitive bundle.

    Must be:
    - immutable
    - declarative
    - invariant-compliant
    """

    # identity
    @property
    def bundle_id(self) -> str:
        ...

    @property
    def generated_at(self) -> datetime:
        ...

    # core cognition
    @property
    def decision(self) -> Optional[DecisionResult]:
        ...

    @property
    def control(self) -> Optional[CognitiveControlSnapshot]:
        ...

    # context
    @property
    def timeline(self) -> Sequence[Any]:
        ...

    @property
    def context_hints(self) -> Dict[str, Any]:
        ...

    @property
    def memory_long(self) -> Optional[Any]:
        ...

    # observability
    @property
    def explanation(self) -> Any:
        ...