# arvis/cognition/conversation/conversation_state.py

from dataclasses import dataclass, field
from typing import Any

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

    last_strategy: ResponseStrategyType | None = None
    strategy_streak: int = 0
    turn_count: int = 0

    last_act: str | None = None

    momentum: float = 0.0

    signals: dict[str, Any] = field(default_factory=dict)

    cognitive_snapshot: dict[str, Any] | None = None
    world_prediction: dict[str, Any] | None = None

    # simplified strategy field (no object dependency)
    strategy_distribution: dict[str, float] = field(default_factory=dict)
