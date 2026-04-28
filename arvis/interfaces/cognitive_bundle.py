# arvis/interfaces/cognitive_bundle.py

from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol

from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot
from arvis.cognition.decision.decision_result import DecisionResult


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
    def bundle_id(self) -> str: ...

    @property
    def generated_at(self) -> datetime: ...

    # core cognition
    @property
    def decision(self) -> DecisionResult | None: ...

    @property
    def control(self) -> CognitiveControlSnapshot | None: ...

    # context
    @property
    def timeline(self) -> Sequence[Any]: ...

    @property
    def context_hints(self) -> dict[str, Any]: ...

    @property
    def memory_long(self) -> Any | None: ...

    # observability
    @property
    def explanation(self) -> Any: ...
