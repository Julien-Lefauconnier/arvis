# arvis/kernel/pipeline/stages/confirmation_stage.py

from __future__ import annotations

from datetime import datetime, timezone

from typing import Any
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.confirmation.confirmation_result import ConfirmationStatus
from arvis.cognition.conflict.conflict_confirmation import requires_conflict_confirmation
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class ConfirmationStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        verdict = ctx.gate_result

        # -----------------------------------------
        # 1. OVERRIDE (user already answered)
        # -----------------------------------------
        if ctx.confirmation_result is not None:

            if ctx.confirmation_result.status == ConfirmationStatus.CONFIRMED:
                verdict = LyapunovVerdict.ALLOW

            elif ctx.confirmation_result.status == ConfirmationStatus.REJECTED:
                verdict = LyapunovVerdict.ABSTAIN

            ctx.gate_result = verdict

        # -----------------------------------------
        # 2. CONFLICT PRESSURE
        # -----------------------------------------
        conflict_pressure = getattr(ctx, "conflict_pressure", None)

        if conflict_pressure is None:
            conflict_pressure = pipeline.conflict_pressure_engine.compute([])

        conflict_requires_confirmation = requires_conflict_confirmation(
            conflict_pressure=conflict_pressure.decisional,
            threshold=0.8,
        )

        # -----------------------------------------
        # 3. NEEDS CONFIRMATION
        # -----------------------------------------
        needs_confirmation = (
            verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
            or (
                verdict == LyapunovVerdict.ALLOW
                and conflict_requires_confirmation
            )
        )

        # -----------------------------------------
        # 4. REQUEST
        # -----------------------------------------
        confirmation_request = None

        if needs_confirmation and ctx.confirmation_result is None:
            confirmation_request = ConfirmationRequest(
                request_id=f"confirm:{ctx.user_id}:{datetime.now(timezone.utc).timestamp()}",
                target_id=str(getattr(ctx.bundle, "bundle_id", "bundle")),
                reason="lyapunov_guard",
            )

        # -----------------------------------------
        # 5. EXPORT
        # -----------------------------------------
        ctx.confirmation_request = confirmation_request
        ctx._needs_confirmation = needs_confirmation