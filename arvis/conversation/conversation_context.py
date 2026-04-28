# arvis/conversation/conversation_context.py

from dataclasses import dataclass, field
from typing import Any, Callable

from arvis.conversation.user_adaptive_profile import UserAdaptiveProfile
from arvis.conversation.conversation_state import ConversationState
from arvis.cognition.gate.cognitive_gate_verdict import CognitiveGateVerdict
from arvis.linguistic.acts.linguistic_act import LinguisticAct
from arvis.conversation.response_strategy_type import ResponseStrategyType


@dataclass
class ConversationContext:
    """
    Mutable runtime context for the conversation orchestration layer.

    This object belongs to the conversation runtime layer, not to the
    kernel-safe declarative cognition layer.
    """

    prompt: str
    act: LinguisticAct | None
    gate_verdict: CognitiveGateVerdict | None
    state: ConversationState

    has_decision: bool = False
    intent_type: str | None = None
    proposed_strategy: ResponseStrategyType | None = None
    control_state: object | None = None

    memory_snapshot: Any | None = None
    memory_write_hook: Callable[..., Any] | None = None

    user_profile: UserAdaptiveProfile | None = None
    long_memory: dict[str, Any] = field(default_factory=dict)
