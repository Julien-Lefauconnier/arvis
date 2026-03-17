# arvis/cognition/observability/symbolic_feature_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolicFeatureSnapshot:
    conflict_entropy: float
    contradiction_density: float
    gate_switch_rate: float
    policy_disagreement_rate: float
    symbolic_drift_score: float

    edges_count: int
    mean_edge_weight: float
    max_edge_weight: float
    spectral_proxy: float