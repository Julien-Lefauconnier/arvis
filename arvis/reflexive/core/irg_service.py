# arivs/reflexive/core/irg_service.py

from __future__ import annotations
from typing import Any, cast
import numpy as np

from .irg_latent_state import IRGLatentState



class IRGService:
    """
    Internal Reflexive Geometry (IRG).

    Maintains a slow latent geometry of the system.
    """

    def __init__(self) -> None:
        self.state = IRGLatentState()
        self.lr = 0.05

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update_from_world(self, snapshot: Any) -> None:
        """
        Update latent geometry from world model.
        """

        collapse, drift, persistence = self._extract(snapshot)

        stability = 1.0 - collapse
        structural = collapse

        target = np.array([stability, structural, persistence, drift])
        current = cast(np.ndarray, self.state.as_vector())

        updated = (1 - self.lr) * current + self.lr * target

        self.state = IRGLatentState(
            stability_memory=float(updated[0]),
            structural_risk=float(updated[1]),
            regime_persistence=float(updated[2]),
            uncertainty_drift=float(updated[3]),
        )

    # ---------------------------------------------------------
    # Snapshot
    # ---------------------------------------------------------

    def snapshot(self) -> IRGLatentState:
        return self.state
    
    def _extract(self, snapshot: Any) -> tuple[float, float, float]:
        """
        Robust ZKCS-safe extractor.
        Supports:
        - OnlineWorldModel.predict()
        - legacy snapshots
        - WorldModelSnapshot
        """

        # OnlineWorldModel path
        if hasattr(snapshot, "collapse_risk"):
            collapse = float(snapshot.collapse_risk)
            drift = float(getattr(snapshot, "uncertainty", 0.5))
            regimes = getattr(snapshot, "regime_probs", {})

            persistence = (
                max(regimes.values()) if regimes else 0.0
            )

            return collapse, drift, persistence

        # WorldModelSnapshot path
        if hasattr(snapshot, "features"):
            f = snapshot.features

            collapse = float(f.collapse_risk or 0.0)
            drift = float(f.uncertainty or 0.5)
            persistence = 0.5  # PoC

            return collapse, drift, persistence

        # fallback safe
        return 0.0, 0.5, 0.0