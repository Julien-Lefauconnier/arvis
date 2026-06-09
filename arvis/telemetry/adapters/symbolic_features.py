# arvis/telemetry/adapters/symbolic_features.py

from __future__ import annotations

from arvis.cognition.observability.symbolic.symbolic_feature_snapshot import (
    SymbolicFeatureSnapshot,
)
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

SYMBOLIC_FEATURES_COMPONENT = "kernel.symbolic_features"


def symbolic_features_event(
    snapshot: SymbolicFeatureSnapshot,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = SYMBOLIC_FEATURES_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """Build a telemetry event from the symbolic feature snapshot.

    ``SymbolicFeatureSnapshot`` exposes graph/statistics features of the
    symbolic conflict structure: conflict entropy, contradiction density,
    gate-switch and policy-disagreement rates, the symbolic drift score and
    the conflict-graph edge statistics. All values are deterministic and
    ZKCS-safe.
    """
    attributes: TelemetryAttributes = {
        "conflict_entropy": snapshot.conflict_entropy,
        "contradiction_density": snapshot.contradiction_density,
        "gate_switch_rate": snapshot.gate_switch_rate,
        "policy_disagreement_rate": snapshot.policy_disagreement_rate,
        "symbolic_drift_score": snapshot.symbolic_drift_score,
        "edges_count": snapshot.edges_count,
        "mean_edge_weight": snapshot.mean_edge_weight,
        "max_edge_weight": snapshot.max_edge_weight,
        "spectral_proxy": snapshot.spectral_proxy,
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="symbolic feature snapshot",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
