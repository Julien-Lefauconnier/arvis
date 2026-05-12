# arvis/kernel/projection/bundle_projection_mapper.py

from arvis.cognition.bundle.cognitive_bundle_snapshot import (
    CognitiveBundleSnapshot,
)
from arvis.math.state.lyapunov_projection_state import (
    LyapunovProjectionState,
)


class BundleProjectionMapper:
    @staticmethod
    def from_bundle(
        bundle: CognitiveBundleSnapshot,
    ) -> LyapunovProjectionState:
        return LyapunovProjectionState(
            conflict_pressure=float(
                getattr(bundle.decision_result, "conflict_pressure", 0.0)
            ),
            drift_score=float(getattr(bundle.decision_result, "drift_score", 0.0)),
            collapse_risk=float(getattr(bundle.decision_result, "collapse_risk", 0.0)),
            confidence=float(getattr(bundle.decision_result, "confidence", 1.0)),
        )
