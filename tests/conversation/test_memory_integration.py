# tests/conversation/test_memory_integration.py

from arvis.conversation.conversation_orchestrator import ConversationOrchestrator
from arvis.memory.memory_long_projector import MemoryLongContextProjector

from tests.conversation.test_act_strategy_pipeline import build_context
from arvis.cognition.gate.cognitive_gate_verdict import CognitiveGateVerdict


def test_memory_injection_into_signals():
    context = build_context(CognitiveGateVerdict.ALLOW)

    class FakeEntry:
        key = "language"

    class FakeSnapshot:
        active_entries = [FakeEntry()]

    context.memory_snapshot = FakeSnapshot()

    ConversationOrchestrator.process(context)

    assert context.state.signals["has_language_pref"] is True


def test_memory_constraints_reduce_action():
    context = build_context(
        CognitiveGateVerdict.ALLOW,
        has_decision=True,
    )

    class FakeEntry:
        key = "no_marketing_emails"

    class FakeSnapshot:
        active_entries = [FakeEntry()]

    context.memory_snapshot = FakeSnapshot()

    plan = ConversationOrchestrator.process(context)

    assert plan.strategy.value in ("confirmation", "informational")


def test_memory_projection_no_payload_leak():
    class FakeEntry:
        key = "language"

    class FakeSnapshot:
        active_entries = [FakeEntry()]

    projector = MemoryLongContextProjector()
    result = projector.project(FakeSnapshot())

    assert "payload_ciphertext" not in result
    assert "nonce" not in result


def test_memory_write_hook_called():
    context = build_context(CognitiveGateVerdict.ALLOW)

    called = {"value": False}

    def hook(**kwargs):
        called["value"] = True

    context.memory_write_hook = hook

    ConversationOrchestrator.process(context)

    assert called["value"] is True


def test_no_memory_snapshot_safe():
    context = build_context(CognitiveGateVerdict.ALLOW)

    plan = ConversationOrchestrator.process(context)

    assert plan is not None
    assert plan.strategy is not None


def test_memory_bridge_propagates_to_kernel():
    context = build_context(CognitiveGateVerdict.ALLOW)

    class FakeEntry:
        key = "no_marketing_emails"

    class FakeSnapshot:
        active_entries = [FakeEntry()]

    context.memory_snapshot = FakeSnapshot()

    ConversationOrchestrator.process(context)

    assert context.long_memory["constraints"] == ["no_marketing_emails"]


# ✅ NEW — adaptive loop integration
def test_adaptive_feedback_loop_integration():
    context = build_context(CognitiveGateVerdict.ALLOW)

    # inject instability signals
    context.state.signals["collapse_risk"] = 0.8
    context.state.signals["uncertainty"] = 0.7

    ConversationOrchestrator.process(context)

    # feedback should exist
    assert "feedback" in context.state.signals

    # adaptive system should not crash and should update weights
    from arvis.conversation.conversation_energy_model import ConversationEnergyModel

    weights = ConversationEnergyModel._dynamic_weights

    assert isinstance(weights, dict)
    assert "collapse" in weights