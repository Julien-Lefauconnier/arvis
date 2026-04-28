# arvis/control/control_context.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class ControlContext:
    """
    Optional control context.

    Kernel invariants:
    - declarative only
    - no execution
    """

    # Search
    search_weights: Optional[Dict[str, float]] = None
    search_strategy: Optional[str] = None

    # Memory
    memory_policy: Optional[str] = None
    memory_write_enabled: Optional[bool] = None

    # AI behavior
    llm_temperature: Optional[float] = None
    llm_creativity: Optional[str] = None

    # Validation
    require_user_validation: Optional[bool] = None

    # Extension
    extras: Dict[str, Any] = field(default_factory=dict)
