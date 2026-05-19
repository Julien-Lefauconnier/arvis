# arvis/kernel/pipeline/stages/execution_stage.py

from __future__ import annotations

from typing import Any

from arvis.kernel.execution.cognitive_execution_state import CognitiveExecutionState
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class ExecutionStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        verdict = ctx.gate_result

        # -------------------------------------------------
        # Runtime execution state bootstrap
        # -------------------------------------------------
        if ctx.execution.execution_state is None:
            ctx.execution.execution_state = CognitiveExecutionState()

        runtime = ctx.execution.execution_state

        # -------------------------------------------------
        # Runtime authority resolution
        # -------------------------------------------------
        # REQUIRE_CONFIRMATION verdict is itself a runtime
        # execution authority signal.
        #
        # ConfirmationStage may also have propagated an
        # explicit runtime.needs_confirmation state.
        # -------------------------------------------------

        needs_confirmation = (
            verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
            or runtime.needs_confirmation
        )

        requires_confirmation = needs_confirmation and ctx.confirmation_result is None

        can_execute = verdict == LyapunovVerdict.ALLOW and not requires_confirmation

        # -------------------------------------------------
        # Execution status resolution
        # -------------------------------------------------
        if can_execute:
            execution_status = ExecutionGateStatus.READY

        elif needs_confirmation:
            execution_status = ExecutionGateStatus.BLOCKED_CONFIRMATION

        elif requires_confirmation:
            execution_status = ExecutionGateStatus.BLOCKED_CONFIRMATION

        else:
            execution_status = ExecutionGateStatus.BLOCKED_ABSTAIN

        # -------------------------------------------------
        # Runtime-owned execution authority
        # -------------------------------------------------
        runtime.needs_confirmation = needs_confirmation
        runtime.requires_confirmation = requires_confirmation
        runtime.can_execute = can_execute
        runtime.execution_status = execution_status

        # -------------------------------------------------
        # Compatibility observability exports
        # -------------------------------------------------
        ctx.extra["needs_confirmation"] = needs_confirmation
        ctx.extra["requires_confirmation"] = requires_confirmation
        ctx.extra["can_execute"] = can_execute
