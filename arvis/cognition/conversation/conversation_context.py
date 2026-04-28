# arvis/cognition/conversation/conversation_context.py

from dataclasses import dataclass

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
    act: str | None

    # gate verdict simplified
    gate_verdict: str | None

    state: ConversationState

    has_decision: bool = False
    intent_type: str | None = None

    proposed_strategy: ResponseStrategyType | None = None

    # Control integration
    control_state: object | None = None
