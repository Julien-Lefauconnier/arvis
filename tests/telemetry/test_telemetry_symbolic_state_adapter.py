# tests/telemetry/test_telemetry_symbolic_state_adapter.py

from arvis.math.state.symbolic_state import SymbolicState
from arvis.telemetry import TelemetryKind
from arvis.telemetry.adapters import SYMBOLIC_STATE_COMPONENT, symbolic_state_event


def test_symbolic_state_event_maps_fields() -> None:
    event = symbolic_state_event(
        SymbolicState(
            intent_type="extraction",
            intent_confidence=0.9,
            gate_verdict="ALLOW",
            conversation_mode="steady",
            conflict_histogram={"semantic": 2},
            conflict_severity=0.3,
            override_count=1,
            override_rate=0.1,
        )
    )
    assert event.kind is TelemetryKind.STABILITY
    assert event.component == SYMBOLIC_STATE_COMPONENT
    assert event.attributes["intent_type"] == "extraction"
    assert event.attributes["gate_verdict"] == "ALLOW"
    assert event.attributes["conflict_histogram"] == {"semantic": 2}
    assert event.attributes["override_count"] == 1


def test_symbolic_state_event_empty_histogram() -> None:
    event = symbolic_state_event(
        SymbolicState(
            intent_type="unknown",
            intent_confidence=1.0,
            gate_verdict="ABSTAIN",
            conversation_mode="unknown",
            conflict_histogram={},
            conflict_severity=0.0,
            override_count=0,
            override_rate=0.0,
        )
    )
    assert event.attributes["conflict_histogram"] == {}
    assert event.attributes["conversation_mode"] == "unknown"
