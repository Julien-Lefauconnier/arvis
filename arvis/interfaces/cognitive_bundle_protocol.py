# arvis/interfaces/cognitive_bundle.py (squelette initial)
"""
Minimal protocol for ARVIS Cognitive Bundles.
"""

from typing import Protocol, Sequence, Dict, Any, Optional
from datetime import datetime


class CognitiveBundle(Protocol):
    """
    Minimal contract for a cognitive bundle.

    Implementations must be:
    - immutable
    - declarative
    - invariant-compliant
    """

    @property
    def generated_at(self) -> datetime:
        ...

    @property
    def explanation(self) -> Any:
        ...

    @property
    def timeline(self) -> Sequence[Any]:
        ...

    @property
    def context_hints(self) -> Dict[str, Any]:
        ...

    @property
    def memory_long(self) -> Optional[Any]:
        ...