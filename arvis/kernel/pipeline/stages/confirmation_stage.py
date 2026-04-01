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
        print("\n[CONFIRMATION DEBUG] START")
        print("incoming gate_result:", getattr(ctx, "gate_result", None))
        print("incoming confirmation_result:", getattr(ctx, "confirmation_result", None))
        print("incoming conflict_pressure:", getattr(ctx, "conflict_pressure", None))

        verdict = ctx.gate_result

        # -----------------------------------------
        # 1. OVERRIDE (user already answered)
        # -----------------------------------------
        if ctx.confirmation_result is not None:

            if ctx.confirmation_result.status == ConfirmationStatus.CONFIRMED:
                verdict = LyapunovVerdict.ALLOW
                ctx.extra["confirmation_override"] = True

            elif ctx.confirmation_result.status == ConfirmationStatus.REJECTED:
                verdict = LyapunovVerdict.ABSTAIN
                ctx.extra["confirmation_override"] = True

            ctx.gate_result = verdict

        print("[CONFIRMATION DEBUG] post-override verdict:", verdict)

        # -----------------------------------------
        # 2. CONFLICT PRESSURE
        # -----------------------------------------
        conflict_pressure = getattr(ctx, "conflict_pressure", None)

        if conflict_pressure is None:
            conflict_pressure = getattr(ctx, "extra", {}).get("conflict_pressure")

        if conflict_pressure is None:
            conflict_pressure = pipeline.conflict_pressure_engine.compute([])

        #  normalize value
        if isinstance(conflict_pressure, (int, float)):
            conflict_value = float(conflict_pressure)
        else:
            conflict_value = getattr(conflict_pressure, "decisional", 0.0)

        conflict_requires_confirmation = requires_conflict_confirmation(
            conflict_pressure=conflict_value,
            threshold=0.8,
        )

        print("[CONFIRMATION DEBUG] conflict_value:", conflict_value)
        print("[CONFIRMATION DEBUG] conflict_requires_confirmation:", conflict_requires_confirmation)

        # -----------------------------------------
        # 2.5 STRUCTURAL RISK (non-math layer)
        # -----------------------------------------
        structural_risk = getattr(ctx, "extra", {}).get("structural_risk", False)

        print("[CONFIRMATION DEBUG] structural_risk:", structural_risk)

        # -----------------------------------------
        # 3. NEEDS CONFIRMATION (include Gate signal)
        # -----------------------------------------
        gate_requires_confirmation = bool(
            getattr(ctx, "extra", {}).get("_requires_confirmation", False)
        )

        needs_confirmation = (
            gate_requires_confirmation
            or verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
            or verdict == LyapunovVerdict.ABSTAIN
            or conflict_requires_confirmation
            or structural_risk
        )

        print("[CONFIRMATION DEBUG] needs_confirmation:", needs_confirmation)

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
        ctx._requires_confirmation = (
            needs_confirmation and ctx.confirmation_result is None
        )

        print("[CONFIRMATION DEBUG] exported _needs_confirmation:", ctx._needs_confirmation)
        print("[CONFIRMATION DEBUG] exported _requires_confirmation:", ctx._requires_confirmation)