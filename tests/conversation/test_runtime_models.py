# tests/conversation/test_runtime_models.py

from arvis.conversation.conversation_context import ConversationContext
from arvis.conversation.conversation_state import ConversationState
from arvis.cognition.gate.cognitive_gate_verdict import CognitiveGateVerdict


def test_runtime_conversation_state_is_mutable():
    state = ConversationState()
    state.cognitive_snapshot = {"ok": True}
    state.signals["collapse_risk"] = 0.2

    assert state.cognitive_snapshot == {"ok": True}
    assert state.signals["collapse_risk"] == 0.2


def test_runtime_conversation_context_accepts_runtime_hooks():
    ctx = ConversationContext(
        prompt="hello",
        act=None,
        gate_verdict=CognitiveGateVerdict.ALLOW,
        state=ConversationState(),
    )

    ctx.memory_snapshot = object()
    ctx.memory_write_hook = lambda **kwargs: None

    assert ctx.memory_snapshot is not None
    assert callable(ctx.memory_write_hook)
