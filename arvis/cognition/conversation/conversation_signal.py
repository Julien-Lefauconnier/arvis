# arvis/cognition/conversation/conversation_signal.py

from dataclasses import dataclass
from typing import Optional

from .response_strategy_type import ResponseStrategyType


@dataclass(frozen=True)
class ConversationSignal:
    """
    Minimal conversational signal snapshot.

    Kernel invariants:
    - immutable
    - no mutation logic
    - no orchestration
    """

    strategy: Optional[ResponseStrategyType]
    turn_count: int
    momentum: float