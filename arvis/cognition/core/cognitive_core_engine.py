# arvis/cognition/core/cognitive_core_engine.py

from typing import Any, Optional

from arvis.cognition.core.cognitive_core_result import CognitiveCoreResult


class CognitiveCoreEngine:
    def __init__(self, core_model: Optional[Any]) -> None:
        self.core_model = core_model

    def process(self, bundle: Any) -> CognitiveCoreResult:
        if self.core_model is None:
            # fallback minimal pour kernel + tests
            return CognitiveCoreResult(
                collapse_risk=0.0,
                dv=0.0,
                core_snapshot=type("CoreSnapshot", (), {})(),
                reflexive_state=None,
            )

        core_snapshot = self.core_model.compute(bundle=bundle)

        # Core exposes current scientific observables.
        # Causal history is owned by the pipeline.

        collapse_risk = (
            getattr(core_snapshot, "fused_risk", None)
            or getattr(core_snapshot, "collapse_risk", 0.0)
        )
        dv = (
            getattr(core_snapshot, "dv", None)
            or getattr(core_snapshot, "drift_score", 0.0)
        )

        reflexive_state = None

        try:
            irg_snapshot = getattr(core_snapshot, "irg_snapshot", None)

            if irg_snapshot:
                reflexive_state = {
                    "stability_memory": getattr(irg_snapshot, "stability_memory", None),
                    "structural_risk": getattr(irg_snapshot, "structural_risk", None),
                    "regime_persistence": getattr(irg_snapshot, "regime_persistence", None),
                    "uncertainty_drift": getattr(irg_snapshot, "uncertainty_drift", None),
                }
            else:
                direct_reflexive = getattr(core_snapshot, "reflexive_state", None)
                if direct_reflexive:
                    reflexive_state = {
                        "stability_memory": direct_reflexive.get("stability_memory", None),
                        "structural_risk": direct_reflexive.get("structural_risk", None),
                        "regime_persistence": direct_reflexive.get("regime_persistence", None),
                        "uncertainty_drift": direct_reflexive.get("uncertainty_drift", None),
                    }
        except Exception:
            reflexive_state = None

        return CognitiveCoreResult(
            collapse_risk=float(collapse_risk or 0.0),
            dv=float(dv or 0.0),
            core_snapshot=core_snapshot,
            reflexive_state=reflexive_state,
        )