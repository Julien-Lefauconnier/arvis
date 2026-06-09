# tests/telemetry/test_telemetry_symbolic_features_adapter.py

from arvis.cognition.observability.symbolic.symbolic_feature_snapshot import (
    SymbolicFeatureSnapshot,
)
from arvis.telemetry import TelemetryKind
from arvis.telemetry.adapters import (
    SYMBOLIC_FEATURES_COMPONENT,
    symbolic_features_event,
)


def test_symbolic_features_event_maps_fields() -> None:
    event = symbolic_features_event(
        SymbolicFeatureSnapshot(
            conflict_entropy=0.1,
            contradiction_density=0.2,
            gate_switch_rate=0.0,
            policy_disagreement_rate=0.05,
            symbolic_drift_score=0.3,
            edges_count=4,
            mean_edge_weight=0.5,
            max_edge_weight=0.9,
            spectral_proxy=0.7,
        )
    )
    assert event.kind is TelemetryKind.STABILITY
    assert event.component == SYMBOLIC_FEATURES_COMPONENT
    assert event.attributes["conflict_entropy"] == 0.1
    assert event.attributes["edges_count"] == 4
    assert event.attributes["spectral_proxy"] == 0.7


def test_symbolic_features_event_zero_edges() -> None:
    event = symbolic_features_event(
        SymbolicFeatureSnapshot(
            conflict_entropy=0.0,
            contradiction_density=0.0,
            gate_switch_rate=0.0,
            policy_disagreement_rate=0.0,
            symbolic_drift_score=0.0,
            edges_count=0,
            mean_edge_weight=0.0,
            max_edge_weight=0.0,
            spectral_proxy=0.0,
        )
    )
    assert event.attributes["edges_count"] == 0
    assert event.attributes["mean_edge_weight"] == 0.0
