# arvis/contracts/cognitive_state_contract.py

from __future__ import annotations

from arvis.cognition.state.cognitive_state import CognitiveState


class CognitiveStateContract:
    """
    Enforces invariants and structural guarantees
    for CognitiveState before IR export.
    """

    @staticmethod
    def validate(state: CognitiveState) -> None:

        # -------------------------
        # REQUIRED FIELDS
        # -------------------------
        assert state.bundle_id, "bundle_id is required"

        # -------------------------
        # NUMERICAL SANITY
        # -------------------------
        assert state.stability.dv is not None and state.stability.dv >= 0.0

        assert 0.0 <= state.control.epsilon <= 1.0, "epsilon out of bounds"

        # -------------------------
        # RISK CONSISTENCY
        # -------------------------
        r = state.risk
        # fused risk must dominate components
        assert r.fused_risk >= max(
            r.mh_risk,
            r.world_risk,
            r.forecast_risk,
        ), "fused_risk must dominate component risks"

        for name in [
            "mh_risk",
            "world_risk",
            "forecast_risk",
            "fused_risk",
            "smoothed_risk",
        ]:
            val = getattr(r, name)
            assert 0.0 <= val <= 1.0, f"{name} must be in [0,1]"

        # -------------------------
        # LOGICAL CONSISTENCY
        # -------------------------
        if r.fused_risk >= 0.75:
            assert r.early_warning is True

        # -------------------------
        # OPTIONAL BLOCK CONSISTENCY
        # -------------------------
        if state.projection is not None:
            if state.projection.valid is False:
                assert state.projection.margin is not None