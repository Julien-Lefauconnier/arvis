# tests/ir/test_cognitive_ir_envelope.py

from arvis.ir.cognitive_ir import CognitiveIR
from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.envelope import CognitiveIREnvelope
from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR
from arvis.ir.input import CognitiveInputIR


def test_cognitive_ir_envelope_build() -> None:
    ir = CognitiveIR(
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
            reason_codes=("ok",),
        ),
        state=None,
        gate=CognitiveGateIR(
            verdict=CognitiveGateVerdictIR.ALLOW,
            bundle_id="bundle-1",
            reason_codes=("ok",),
        ),
    )

    serialized = {"gate": {"verdict": "allow"}}
    hash_value = "abc123"

    envelope = CognitiveIREnvelope.build(
        ir=ir,
        serialized=serialized,
        hash_value=hash_value,
    )

    assert envelope.ir is ir
    assert envelope.serialized == serialized
    assert envelope.hash == hash_value
    assert envelope.version == "arvis.ir.envelope.v1"