# arvis/ir/context.py

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CognitiveContextIR:
    """
    Declarative context (non-decision).
    """

    user_id: str
    session_id: str | None = None
    conversation_mode: str | None = None

    long_memory_constraints: tuple[str, ...] = ()
    long_memory_preferences: Mapping[str, Any] = field(default_factory=dict)

    extra: Mapping[str, Any] = field(default_factory=dict)