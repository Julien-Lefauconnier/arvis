# arvis/cognition/conversation/conversation_state.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .response_strategy_type import ResponseStrategyType


@dataclass(frozen=True)
class ConversationState:
    """
    Declarative snapshot of conversational state.

    Kernel invariants:
    - immutable
    - no update logic
    - no orchestration
    """

    last_strategy: Optional[ResponseStrategyType] = None
    strategy_streak: int = 0
    turn_count: int = 0

    last_act: Optional[str] = None

    momentum: float = 0.0

    signals: Dict[str, Any] = field(default_factory=dict)

    cognitive_snapshot: Optional[Dict[str, Any]] = None
    world_prediction: Optional[Dict[str, Any]] = None

    # simplified strategy field (no object dependency)
    strategy_distribution: Dict[str, float] = field(default_factory=dict)