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

    # -----------------------------------------------------
    # ZK-safe memory projection
    # -----------------------------------------------------
    # Important:
    # - no raw memory payload
    # - no entry list
    # - no value exposure
    # Only stable projected signals may appear here.
    memory_present: bool = False
    memory_pressure: float = 0.0
    memory_has_constraints: bool = False
    memory_constraint_count: int = 0
    memory_has_language_pref: bool = False
    memory_has_timezone: bool = False

    extra: Mapping[str, Any] = field(default_factory=dict)
