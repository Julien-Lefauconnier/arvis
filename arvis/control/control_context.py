# arvis/control/control_context.py

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ControlContext:
    """
    Optional control context.

    Kernel invariants:
    - declarative only
    - no execution
    """

    # Search
    search_weights: dict[str, float] | None = None
    search_strategy: str | None = None

    # Memory
    memory_policy: str | None = None
    memory_write_enabled: bool | None = None

    # AI behavior
    llm_temperature: float | None = None
    llm_creativity: str | None = None

    # Validation
    require_user_validation: bool | None = None

    # Extension
    extras: dict[str, Any] = field(default_factory=dict)
