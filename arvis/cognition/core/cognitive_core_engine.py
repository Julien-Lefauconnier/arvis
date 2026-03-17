# arvis/cognition/core/cognitive_core_engine.py

from arvis.cognition.core.cognitive_core_result import CognitiveCoreResult


class CognitiveCoreEngine:
    def __init__(self, core_model):
        self.core_model = core_model

    def process(self, bundle) -> CognitiveCoreResult:
        core_snapshot = self.core_model.compute(bundle=bundle)

        collapse_risk = getattr(core_snapshot, "fused_risk", 0.0)
        dv = getattr(core_snapshot, "dv", 0.0)

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
        except Exception:
            reflexive_state = None

        return CognitiveCoreResult(
            collapse_risk=float(collapse_risk or 0.0),
            dv=float(dv or 0.0),
            core_snapshot=core_snapshot,
            reflexive_state=reflexive_state,
        )