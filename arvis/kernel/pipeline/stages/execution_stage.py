# arvis/kernel/pipeline/stages/execution_stage.py

from __future__ import annotations

from typing import Any
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class ExecutionStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        verdict = ctx.gate_result
        needs_confirmation = getattr(ctx, "_needs_confirmation", False)

        requires_confirmation = needs_confirmation and ctx.confirmation_result is None

        can_execute = verdict == LyapunovVerdict.ALLOW and not requires_confirmation

        if can_execute:
            execution_status = ExecutionGateStatus.READY

        elif requires_confirmation:
            execution_status = ExecutionGateStatus.BLOCKED_CONFIRMATION

        else:
            execution_status = ExecutionGateStatus.BLOCKED_ABSTAIN

        ctx._needs_confirmation = needs_confirmation
        ctx._requires_confirmation = requires_confirmation
        ctx._can_execute = can_execute
        ctx.execution_status = execution_status
