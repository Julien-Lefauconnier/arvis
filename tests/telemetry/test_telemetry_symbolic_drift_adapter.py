# tests/telemetry/test_telemetry_symbolic_drift_adapter.py

from arvis.cognition.observability.symbolic.symbolic_drift_snapshot import (
    SymbolicDriftSnapshot,
    SymbolicRegime,
)
from arvis.telemetry import TelemetryKind
from arvis.telemetry.adapters import SYMBOLIC_DRIFT_COMPONENT, symbolic_drift_event


def test_symbolic_drift_event_maps_fields() -> None:
    event = symbolic_drift_event(
        SymbolicDriftSnapshot(
            drift_score=0.2,
            regime=SymbolicRegime.OK,
            intent_switch=False,
            gate_switch=False,
            confidence_delta=0.0,
            conflict_delta=0.1,
            override_rate=0.0,
        )
    )
    assert event.kind is TelemetryKind.STABILITY
    assert event.component == SYMBOLIC_DRIFT_COMPONENT
    assert event.attributes["drift_score"] == 0.2
    assert event.attributes["regime"] == "ok"
    assert event.attributes["intent_switch"] is False


def test_symbolic_drift_event_regime_serialized_as_str() -> None:
    event = symbolic_drift_event(
        SymbolicDriftSnapshot(
            drift_score=0.8,
            regime=SymbolicRegime.WARNING,
            intent_switch=True,
            gate_switch=True,
            confidence_delta=-0.1,
            conflict_delta=0.5,
            override_rate=0.2,
        )
    )
    assert event.attributes["regime"] == "warning"
    assert isinstance(event.attributes["regime"], str)
