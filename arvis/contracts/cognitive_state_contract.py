# arvis/contracts/cognitive_state_contract.py

from __future__ import annotations

from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.errors.base import ArvisInvariantViolation, ErrorDomain
from arvis.errors.codes import ErrorCode


def _contract_violation(
    message: str,
    *,
    field: str,
    reason: str,
) -> ArvisInvariantViolation:
    return ArvisInvariantViolation(
        message,
        code=ErrorCode.PIPELINE_EXECUTION_CONTRACT_VIOLATION,
        domain=ErrorDomain.PIPELINE,
        details={
            "component": "CognitiveStateContract",
            "field": field,
            "reason": reason,
            "retry_class": "permanent",
        },
    )


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
        if not state.bundle_id:
            raise _contract_violation(
                "bundle_id is required",
                field="bundle_id",
                reason="missing_required_field",
            )

        # -------------------------
        # NUMERICAL SANITY
        # -------------------------
        if state.stability is None:
            raise _contract_violation(
                "stability is required",
                field="stability",
                reason="missing_required_block",
            )

        if state.stability.dv is None:
            raise _contract_violation(
                "stability.dv is required",
                field="stability.dv",
                reason="missing_required_field",
            )

        if state.stability.dv < 0.0:
            raise _contract_violation(
                "stability.dv must be >= 0.0",
                field="stability.dv",
                reason="negative_value",
            )

        if not 0.0 <= state.control.epsilon <= 1.0:
            raise _contract_violation(
                "epsilon out of bounds",
                field="control.epsilon",
                reason="out_of_bounds",
            )

        # -------------------------
        # RISK CONSISTENCY
        # -------------------------
        r = state.risk
        # fused risk must dominate components
        if r.fused_risk < max(
            r.mh_risk,
            r.world_risk,
            r.forecast_risk,
        ):
            raise _contract_violation(
                "fused_risk must dominate component risks",
                field="risk.fused_risk",
                reason="risk_consistency_violation",
            )

        for name in [
            "mh_risk",
            "world_risk",
            "forecast_risk",
            "fused_risk",
            "smoothed_risk",
        ]:
            val = getattr(r, name)
            if not 0.0 <= val <= 1.0:
                raise _contract_violation(
                    f"{name} must be in [0,1]",
                    field=f"risk.{name}",
                    reason="out_of_bounds",
                )

        # -------------------------
        # LOGICAL CONSISTENCY
        # -------------------------
        if r.fused_risk >= 0.75:
            if r.early_warning is not True:
                raise _contract_violation(
                    "early_warning required when fused_risk >= 0.75",
                    field="risk.early_warning",
                    reason="missing_early_warning",
                )

        # -------------------------
        # OPTIONAL BLOCK CONSISTENCY
        # -------------------------
        if state.projection is not None:
            if state.projection.valid is False:
                if state.projection.margin is None:
                    raise _contract_violation(
                        "projection.margin required when projection is invalid",
                        field="projection.margin",
                        reason="missing_projection_margin",
                    )

        # -------------------------
        # TIMELINE SAFETY
        # -------------------------
        if state.timeline is not None:
            if not hasattr(state.timeline, "list_signals"):
                raise _contract_violation(
                    "timeline must expose list_signals",
                    field="timeline",
                    reason="invalid_timeline_interface",
                )
