# arvis/kernel/pipeline/stages/confirmation_stage.py

from __future__ import annotations

from typing import Any

from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.confirmation.confirmation_result import ConfirmationStatus
from arvis.cognition.conflict.conflict_confirmation import (
    requires_conflict_confirmation,
)
from arvis.kernel.execution.cognitive_execution_state import CognitiveExecutionState
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.types.identifiers import deterministic_id


class ConfirmationStage:
    def _debug(self, ctx: Any, *parts: object) -> None:
        if not getattr(ctx, "debug", False):
            return

        extra = getattr(ctx, "extra", None)
        if not isinstance(extra, dict):
            return

        extra.setdefault("debug_events", []).append(
            " ".join(str(part) for part in parts)
        )

    def run(self, pipeline: Any, ctx: Any) -> None:
        self._debug(ctx, "\n[CONFIRMATION DEBUG] START")
        self._debug(
            ctx,
            "incoming gate_result:",
            getattr(ctx, "gate_result", None),
        )
        self._debug(
            ctx,
            "incoming confirmation_result:",
            getattr(ctx, "confirmation_result", None),
        )
        self._debug(
            ctx,
            "incoming conflict_pressure:",
            getattr(ctx, "conflict_pressure", None),
        )

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

        self._debug(
            ctx,
            "[CONFIRMATION DEBUG] post-override verdict:",
            verdict,
        )

        # -----------------------------------------
        # 2. CONFLICT PRESSURE
        # -----------------------------------------
        conflict_pressure = getattr(ctx, "conflict_pressure", None)

        if conflict_pressure is None:
            conflict_pressure = getattr(
                ctx,
                "extra",
                {},
            ).get("conflict_pressure")

        if conflict_pressure is None:
            conflict_pressure = pipeline.conflict_pressure_engine.compute([])

        #  normalize value
        if isinstance(conflict_pressure, (int, float)):
            conflict_value = float(conflict_pressure)
        else:
            conflict_value = getattr(
                conflict_pressure,
                "decisional",
                0.0,
            )

        conflict_requires_confirmation = requires_conflict_confirmation(
            conflict_pressure=conflict_value,
            threshold=0.8,
        )

        self._debug(
            ctx,
            "[CONFIRMATION DEBUG] conflict_value:",
            conflict_value,
        )
        self._debug(
            ctx,
            "[CONFIRMATION DEBUG] conflict_requires_confirmation:",
            conflict_requires_confirmation,
        )

        # -----------------------------------------
        # 2.5 STRUCTURAL RISK (non-math layer)
        # -----------------------------------------
        structural_risk = getattr(
            ctx,
            "extra",
            {},
        ).get("structural_risk", False)

        self._debug(
            ctx,
            "[CONFIRMATION DEBUG] structural_risk:",
            structural_risk,
        )

        # -----------------------------------------
        # 3. NEEDS CONFIRMATION (include Gate signal)
        # -----------------------------------------
        if ctx.execution_state is None:
            ctx.execution_state = CognitiveExecutionState()

        runtime = ctx.execution_state

        gate_requires_confirmation = runtime.requires_confirmation

        needs_confirmation = (
            gate_requires_confirmation
            or verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
            or conflict_requires_confirmation
            or structural_risk
        )

        self._debug(
            ctx,
            "[CONFIRMATION DEBUG] needs_confirmation:",
            needs_confirmation,
        )

        requires_confirmation = needs_confirmation and ctx.confirmation_result is None

        # -----------------------------------------
        # 4. REQUEST
        # -----------------------------------------
        confirmation_request = None

        if needs_confirmation and ctx.confirmation_result is None:
            reason = "lyapunov_guard"
            confirmation_request = ConfirmationRequest(
                request_id=deterministic_id(
                    "confirm",
                    ctx.user_id,
                    getattr(
                        ctx.decision_layer.bundle,
                        "bundle_id",
                        "bundle",
                    ),
                    reason,
                ),
                target_id=str(ctx.decision_layer.bundle_id),
                reason=reason,
            )

        # -----------------------------------------
        # 5. EXPORT
        # -----------------------------------------
        ctx.confirmation_request = confirmation_request

        # -------------------------------------------------
        # Runtime-owned execution authority
        # -------------------------------------------------
        runtime.needs_confirmation = needs_confirmation
        runtime.requires_confirmation = requires_confirmation
        runtime.metadata["confirmation_required"] = requires_confirmation
        runtime.metadata["confirmation_needed"] = needs_confirmation

        # -------------------------------------------------
        # Compatibility projection handled centrally by
        # PipelineExecutionSyncService.
        # -------------------------------------------------

        self._debug(
            ctx,
            "[CONFIRMATION DEBUG] runtime.needs_confirmation:",
            runtime.needs_confirmation,
        )
        self._debug(
            ctx,
            "[CONFIRMATION DEBUG] runtime.requires_confirmation:",
            runtime.requires_confirmation,
        )
