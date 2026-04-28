# arvis/cognition/conversation/conversation_context.py

from dataclasses import dataclass
from typing import Optional

from .conversation_state import ConversationState
from .response_strategy_type import ResponseStrategyType


@dataclass(frozen=True)
class ConversationContext:
    """
    Declarative conversational context.

    Kernel invariants:
    - no execution
    - no dependency on external systems
    """

    prompt: str

    # abstracted act (string instead of object)
    act: Optional[str]

    # gate verdict simplified
    gate_verdict: Optional[str]

    state: ConversationState

    has_decision: bool = False
    intent_type: Optional[str] = None

    proposed_strategy: Optional[ResponseStrategyType] = None

    # Control integration
    control_state: Optional[object] = None
