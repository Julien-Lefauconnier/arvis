# arvis/conversation/conversation_state.py

from dataclasses import dataclass, field
from typing import Any, Optional

from arvis.cognition.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.user_adaptive_profile import UserAdaptiveProfile


@dataclass
class ConversationState:
    """
    Mutable runtime conversation state.
    """

    last_strategy: ResponseStrategyType | None = None
    strategy_streak: int = 0
    turn_count: int = 0
    last_act: str | None = None
    momentum: float = 0.0

    signals: dict[str, Any] = field(default_factory=dict)
    cognitive_snapshot: Any | None = None
    world_prediction: Any | None = None
    strategy_distribution: dict[ResponseStrategyType, float] = field(default_factory=dict)
    user_profile: Optional[UserAdaptiveProfile] = None

    def update_strategy(
        self,
        strategy: ResponseStrategyType,
        collapse_risk: float | None = None,
    ) -> None:
        if self.last_strategy == strategy:
            self.strategy_streak += 1
        else:
            self.strategy_streak = 1

        self.last_strategy = strategy
        self.turn_count += 1

        if collapse_risk is not None:
            self.signals["collapse_risk"] = collapse_risk

        self.strategy_distribution = {
            strategy: 1.0,
        }