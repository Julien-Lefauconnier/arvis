# arvis/cognition/core/cognitive_core_engine.py

import inspect
from typing import Any

from arvis.cognition.core.cognitive_core_result import CognitiveCoreResult


class CognitiveCoreEngine:
    def __init__(self, core_model: Any | None) -> None:
        self.core_model = core_model

    def process(self, bundle: Any, prior: Any | None = None) -> CognitiveCoreResult:
        if self.core_model is None:
            # fallback minimal pour kernel + tests
            return CognitiveCoreResult(
                collapse_risk=0.0,
                dv=0.0,
                core_snapshot=type("CoreSnapshot", (), {})(),
                reflexive_state=None,
            )

        # Backward compatible call: legacy cores expose compute(bundle)
        # returning a single snapshot; stateful cores expose
        # compute(bundle, prior) returning (snapshot, next_state).
        compute = self.core_model.compute
        try:
            accepts_prior = len(inspect.signature(compute).parameters) >= 2
        except (TypeError, ValueError):
            accepts_prior = False

        core_output = (
            compute(bundle, prior) if accepts_prior else compute(bundle=bundle)
        )

        if isinstance(core_output, tuple) and len(core_output) == 2:
            core_snapshot, next_state = core_output
        else:
            core_snapshot, next_state = core_output, None

        # Core exposes current scientific observables.
        # Causal history is owned by the pipeline.

        collapse_risk = getattr(core_snapshot, "fused_risk", None) or getattr(
            core_snapshot, "collapse_risk", 0.0
        )
        dv = getattr(core_snapshot, "dv", None) or getattr(
            core_snapshot, "drift_score", 0.0
        )

        reflexive_state = None

        try:
            irg_snapshot = getattr(core_snapshot, "irg_snapshot", None)

            if irg_snapshot:
                reflexive_state = {
                    "stability_memory": getattr(irg_snapshot, "stability_memory", None),
                    "structural_risk": getattr(irg_snapshot, "structural_risk", None),
                    "regime_persistence": getattr(
                        irg_snapshot, "regime_persistence", None
                    ),
                    "uncertainty_drift": getattr(
                        irg_snapshot, "uncertainty_drift", None
                    ),
                }
            else:
                direct_reflexive = getattr(core_snapshot, "reflexive_state", None)
                if direct_reflexive:
                    reflexive_state = {
                        "stability_memory": direct_reflexive.get(
                            "stability_memory", None
                        ),
                        "structural_risk": direct_reflexive.get(
                            "structural_risk", None
                        ),
                        "regime_persistence": direct_reflexive.get(
                            "regime_persistence", None
                        ),
                        "uncertainty_drift": direct_reflexive.get(
                            "uncertainty_drift", None
                        ),
                    }
        except Exception:
            reflexive_state = None

        return CognitiveCoreResult(
            collapse_risk=float(collapse_risk or 0.0),
            dv=float(dv or 0.0),
            core_snapshot=core_snapshot,
            reflexive_state=reflexive_state,
            next_scientific_state=next_state,
        )
