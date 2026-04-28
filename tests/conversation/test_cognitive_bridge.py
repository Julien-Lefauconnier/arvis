# tests/conversation/test_cognitive_bridge.py

import pytest

from arvis.conversation.conversation_cognitive_bridge import (
    ConversationCognitiveBridge,
)
from arvis.conversation.conversation_stability_signals import (
    ConversationStabilitySignalsBuilder,
)
from arvis.conversation.conversation_state import ConversationState


# --------------------------------------------------
# Fixtures
# --------------------------------------------------


@pytest.fixture(autouse=True)
def reset_bridge():
    """
    Ensure test isolation (no global service leakage).
    """
    ConversationCognitiveBridge.register(None)
    yield
    ConversationCognitiveBridge.register(None)


# --------------------------------------------------
# Dummy objects
# --------------------------------------------------


class DummySnapshot:
    def __init__(self, delta_v):
        self.delta_v = delta_v
        self.fused_risk = abs(delta_v)


class DummyService:
    def compute(self, **kwargs):
        return DummySnapshot(delta_v=-0.3)


class DummyContext:
    class State:
        def __init__(self):
            self.signals = {}
            self.cognitive_snapshot = None

    def __init__(self):
        self.prompt = "test"
        self.state = self.State()


# --------------------------------------------------
# Tests
# --------------------------------------------------


def test_cognitive_bridge_fallback():
    ctx = DummyContext()

    snapshot = ConversationCognitiveBridge.evaluate(ctx)

    assert snapshot is None
    assert ctx.state.signals["collapse_risk"] == 0.0
    assert ctx.state.signals["delta_v"] == 0.0


def test_delta_v_propagation_from_snapshot():
    ctx = DummyContext()

    ConversationCognitiveBridge.register(DummyService())
    ConversationCognitiveBridge.evaluate(ctx)

    assert "delta_v" in ctx.state.signals
    assert ctx.state.signals["delta_v"] == -0.3


def test_delta_v_fallback_without_service():
    ctx = DummyContext()

    ConversationCognitiveBridge.register(None)
    ConversationCognitiveBridge.evaluate(ctx)

    assert ctx.state.signals["delta_v"] == 0.0


def test_regime_changes_with_negative_delta_v():
    state = ConversationState()
    builder = ConversationStabilitySignalsBuilder()

    # simulate stable convergence
    for _ in range(20):
        state.signals["delta_v"] = -0.1
        builder.update(state)

    assert state.signals["regime"] in ["stable", "oscillatory"]
