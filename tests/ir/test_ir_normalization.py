# tests/ir/test_ir_normalization.py

from arvis.ir.normalization.cognitive_ir_normalizer import CognitiveIRNormalizer
from arvis.ir.serialization.cognitive_ir_hasher import CognitiveIRHasher
from arvis.ir.serialization.cognitive_ir_serializer import CognitiveIRSerializer

from arvis.ir.input import CognitiveInputIR
from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR
from arvis.ir.cognitive_ir import CognitiveIR


# -----------------------------------------
# Helpers
# -----------------------------------------

def make_ir(reason_codes=("a", "b"), projection=None, validity=None):
    return CognitiveIR(
        input=CognitiveInputIR(
            input_id="input-1",
            actor_id="user-1",
            surface_kind="chat",
            intent_hint=None,
            metadata={},
        ),
        context=CognitiveContextIR(
            user_id="user-1",
            session_id="session-1",
            conversation_mode=None,
            long_memory_constraints=(),
            long_memory_preferences={},
            extra={},
        ),
        decision=CognitiveDecisionIR(
            decision_id="decision-1",
            decision_kind="informational",
            memory_intent="none",
            reason_codes=reason_codes,
        ),
        state=None,
        gate=CognitiveGateIR(
            verdict=CognitiveGateVerdictIR.ALLOW,
            bundle_id="bundle-1",
            reason_codes=reason_codes,
        ),
        stability=None,
        adaptive=None,
        projection=projection,
        validity=validity,
    )

def hash_ir(ir):
    return CognitiveIRHasher.hash(ir)

class DummyProjection:
    def __init__(self, value="p"):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, DummyProjection) and self.value == other.value


class DummyValidity:
    def __init__(self, value="v"):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, DummyValidity) and self.value == other.value
    


# -----------------------------------------
# Tests
# -----------------------------------------

def test_ir_normalization_is_order_invariant():
    ir1 = make_ir(reason_codes=("b", "a"))
    ir2 = make_ir(reason_codes=("a", "b"))

    norm1 = CognitiveIRNormalizer.normalize(ir1)
    norm2 = CognitiveIRNormalizer.normalize(ir2)

    assert norm1 == norm2


def test_ir_hash_stability():
    norm = CognitiveIRNormalizer.normalize(make_ir())

    hash1 = hash_ir(norm)
    hash2 = hash_ir(norm)

    assert hash1 == hash2


def test_ir_normalization_idempotent():
    ir = make_ir(reason_codes=("b", "a"))

    norm1 = CognitiveIRNormalizer.normalize(ir)
    norm2 = CognitiveIRNormalizer.normalize(norm1)

    assert norm1 == norm2


def test_ir_preserves_projection_and_validity():
    ir = make_ir(
        projection=DummyProjection("proj"),
        validity=DummyValidity("valid"),
    )

    normalized = CognitiveIRNormalizer.normalize(ir)

    assert normalized.projection == ir.projection
    assert normalized.validity == ir.validity


def test_ir_hash_includes_projection_and_validity():
    ir = make_ir(
        projection=DummyProjection("proj"),
        validity=DummyValidity("valid"),
    )

    normalized = CognitiveIRNormalizer.normalize(ir)
    serialized = CognitiveIRSerializer.serialize(normalized)

    assert "projection" in serialized
    assert "validity" in serialized