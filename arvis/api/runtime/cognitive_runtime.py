# arvis/api/runtime/cognitive_runtime.py

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, Optional

from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel_core.process import (
    CognitiveBudget,
    CognitivePriority,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)
from arvis.kernel_core.process.process_factory import ProcessFactory
from arvis.kernel_core.syscalls.service_registry import (
    KernelServiceRegistry,
)
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.runtime import (
    CognitiveRuntimeState,
    CognitiveScheduler,
    PipelineExecutor,
)
from arvis.runtime.process_hooks import ProcessHookManager


@dataclass(frozen=True)
class RuntimeExecutionResult:
    result: Any
    state: Optional[CognitiveState]


class CognitiveRuntime:
    def __init__(
        self,
        pipeline: CognitivePipeline,
        adapters: Optional[Dict[str, Any]] = None,
        tool_executor: Optional[Any] = None,
    ) -> None:
        self.pipeline = pipeline
        self.adapters = adapters or {}
        self.tool_executor = tool_executor
        self.runtime_state = CognitiveRuntimeState()

        self.hooks = ProcessHookManager(runtime_state=self.runtime_state)
        self.process_executor = PipelineExecutor(self.pipeline)
        self.scheduler = CognitiveScheduler(
            runtime_state=self.runtime_state,
            process_executor=self.process_executor,
            hooks=self.hooks,
        )
        self.services = KernelServiceRegistry(
            tool_executor=self.tool_executor,
            vfs_service=None,
            zip_ingest_service=None,
        )
        self.syscall_handler = SyscallHandler(
            runtime_state=self.runtime_state,
            scheduler=self.scheduler,
            services=self.services,
        )

    def execute(
        self,
        ctx: CognitivePipelineContext,
    ) -> RuntimeExecutionResult:
        if self.adapters:
            ctx.extra["adapters"] = self.adapters

        process = ProcessFactory.create(
            process_id=CognitiveProcessId(
                f"proc::{ctx.user_id}::{len(self.runtime_state.processes)}"
            ),
            kind=CognitiveProcessKind.USER_REQUEST,
            status=CognitiveProcessStatus.READY,
            priority=CognitivePriority(50.0),
            budget=CognitiveBudget(
                reasoning_steps=(2 * len(list(self.pipeline.iter_stages()))),
                time_slice_ms=100,
            ),
            created_tick=(self.runtime_state.scheduler_state.tick_count),
            user_id=ctx.user_id,
            local_state=ctx,
        )

        self.scheduler.enqueue(process)

        result = None
        for _ in range(100):
            decision = self.scheduler.tick()
            selected_id = decision.selected_process_id

            if selected_id is None:
                break

            proc = self.runtime_state.get_process(selected_id)
            if self._is_exit_process_state(proc):
                result = self._extract_exit_result(
                    proc,
                    decision,
                )
                break

        if result is None:
            raise RuntimeError("Execution did not produce any result")

        self._execute_tool_if_needed(
            ctx=ctx,
            process=process,
            result=result,
        )

        return RuntimeExecutionResult(
            result=result,
            state=ctx.cognitive_state,
        )

    def _execute_tool_if_needed(
        self,
        *,
        ctx: CognitivePipelineContext,
        process: Any,
        result: Any,
    ) -> None:
        action = getattr(result, "action_decision", None)
        effective_result = result

        force_tool = ctx.extra.get("force_tool")
        force_execution = ctx.extra.get(
            "_force_execution",
            False,
        )

        if action and force_tool and action.tool == force_tool and force_execution:
            forced_action = SimpleNamespace(**dict(action.__dict__))
            forced_action.allowed = True
            forced_action.requires_confirmation = False
            forced_action.can_execute = True

            effective_result = SimpleNamespace(**dict(result.__dict__))
            effective_result.action_decision = forced_action
            action = forced_action

        if not (
            action
            and getattr(action, "tool", None)
            and getattr(action, "allowed", False)
        ):
            return

        syscall_result = self.syscall_handler.handle(
            Syscall(
                name="tool.execute",
                args={
                    "result": effective_result,
                    "ctx": ctx,
                    "process_id": process.process_id.value,
                },
            )
        )

        if not syscall_result.success:
            ctx.extra.setdefault(
                "errors",
                [],
            ).append("tool_execution_failure")

    def _is_exit_process_state(
        self,
        proc: Any,
    ) -> bool:
        return proc.status in (
            CognitiveProcessStatus.COMPLETED,
            CognitiveProcessStatus.WAITING_CONFIRMATION,
            CognitiveProcessStatus.BLOCKED,
            CognitiveProcessStatus.ABORTED,
        )

    def _extract_exit_result(
        self,
        proc: Any,
        decision: Any,
    ) -> Any:
        if proc.status == CognitiveProcessStatus.ABORTED:
            error = proc.last_error or "unknown_error"
            raise RuntimeError(f"Process aborted: {error}")

        if proc.status in (
            CognitiveProcessStatus.COMPLETED,
            CognitiveProcessStatus.WAITING_CONFIRMATION,
            CognitiveProcessStatus.BLOCKED,
        ):
            if proc.last_result is None:
                raise RuntimeError(
                    f"Process exited in state {proc.status.value} without result"
                )
            return proc.last_result

        if getattr(decision, "result", None) is not None:
            return decision.result

        raise RuntimeError("Execution exited without resolvable result")
