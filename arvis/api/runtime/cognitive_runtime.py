# arvis/api/runtime/cognitive_runtime.py

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from arvis.adapters.tools.gates import ConsentGate, EgressGate
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.errors.runtime_execution import (
    ProcessExecutionAborted,
    RuntimeExecutionContractViolation,
    RuntimeExecutionError,
)
from arvis.kernel.execution.cognitive_execution_state import (
    CognitiveExecutionState,
)
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.runtime_bindings import PipelineRuntimeBindings
from arvis.kernel_core.host_declaration import instance_label_of
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
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.cognitive_scheduler import CognitiveScheduler
from arvis.runtime.pipeline_executor import PipelineExecutor
from arvis.runtime.process_hooks import ProcessHookManager
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.retry_policy import ToolRetryPolicy


@dataclass(frozen=True)
class RuntimeExecutionResult:
    result: Any
    state: CognitiveState | None


class CognitiveRuntime:
    def __init__(
        self,
        pipeline: CognitivePipeline,
        adapters: dict[str, Any] | None = None,
        tool_executor: Any | None = None,
        tool_registry: ToolRegistry | None = None,
        consent_gate: ConsentGate | None = None,
        egress_gate: EgressGate | None = None,
        require_gates: bool = False,
        audit_intent_sink: Any | None = None,
        require_durable_intent_sink: bool = False,
        confirmation_registry: Any | None = None,
        host_context: dict[str, Any] | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.adapters = adapters or {}
        self.tool_registry = tool_registry or ToolRegistry()
        self.tool_executor = tool_executor or ToolExecutor(self.tool_registry)
        self.runtime_state = CognitiveRuntimeState()

        self.hooks = ProcessHookManager(runtime_state=self.runtime_state)
        self.process_executor = PipelineExecutor(self.pipeline)
        self.scheduler = CognitiveScheduler(
            runtime_state=self.runtime_state,
            process_executor=self.process_executor,
            hooks=self.hooks,
        )

        self.tool_manager = ToolManager(
            registry=self.tool_registry,
            executor=self.tool_executor,
            consent_gate=consent_gate,
            egress_gate=egress_gate,
            require_gates=require_gates,
            confirmation_registry=confirmation_registry,
        )
        self.tool_retry_policy = ToolRetryPolicy()
        self.services = KernelServiceRegistry(
            tool_executor=self.tool_executor,
            tool_manager=self.tool_manager,
            vfs_service=None,
            zip_ingest_service=None,
            llm_adapter=self.adapters.get("llm"),
            audit_intent_sink=audit_intent_sink,
            require_durable_intent_sink=require_durable_intent_sink,
            # Campaign 5 (D-1): opaque host context and the instance
            # label ARVIS stamps from it, opaque otherwise.
            host_context=host_context,
            instance_label=instance_label_of(host_context),
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
            ctx.runtime_bindings.adapters = self.adapters

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

        ctx.runtime_bindings.syscall_handler = self.syscall_handler
        ctx.runtime_bindings.process_id = process.process_id.value

        runtime_bindings = PipelineRuntimeBindings(
            syscall_handler=self.syscall_handler,
            process_id=process.process_id.value,
        )

        ctx.runtime_bindings.runtime = runtime_bindings

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
            raise RuntimeExecutionError("Execution did not produce any result")

        self._execute_tool_if_needed(
            ctx=ctx,
            process=process,
            result=result,
        )

        return RuntimeExecutionResult(
            result=result,
            state=ctx.cognitive_state,
        )

    # ---------------------------------------------------------
    # Runtime execution state ownership
    # ---------------------------------------------------------
    #
    # Some runtime-direct execution paths bypass the full
    # pipeline bootstrap lifecycle.
    #
    # Runtime remains authoritative for ensuring that
    # execution_state exists before syscall orchestration.
    # ---------------------------------------------------------
    def _ensure_execution_state(
        self,
        ctx: CognitivePipelineContext,
    ) -> CognitiveExecutionState:
        execution = getattr(ctx, "execution", None)

        if execution is None:
            raise RuntimeExecutionContractViolation(
                "pipeline context missing execution context"
            )

        runtime = getattr(execution, "execution_state", None)

        if runtime is None:
            runtime = CognitiveExecutionState()
            execution.execution_state = runtime

        return runtime

    def _execute_tool_if_needed(
        self,
        *,
        ctx: CognitivePipelineContext,
        process: Any,
        result: Any,
    ) -> None:
        action = getattr(result, "action_decision", None)
        effective_result = result

        # ---------------------------------------------------------
        # Runtime-owned retry policy state
        # ---------------------------------------------------------
        runtime_policy = getattr(ctx, "runtime_policy", None)
        retry_policy = self.tool_retry_policy

        runtime_policy = getattr(ctx, "runtime_policy", None)

        force_tool = runtime_policy.force_tool if runtime_policy is not None else None

        force_execution = (
            runtime_policy.force_execution if runtime_policy is not None else False
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

        # ---------------------------------------------------------
        #  syscall-governed retry orchestration
        # ---------------------------------------------------------
        #
        # IMPORTANT:
        # - retries MUST pass again through syscall layer
        # - every retry MUST emit:
        #   - new syscall_id
        #   - new causal chain
        #   - new artifact
        #   - new runtime event
        # - ToolManager is intentionally stateless
        # ---------------------------------------------------------

        max_attempts = 3
        attempts = 0
        retry_chain_id: str | None = None
        parent_syscall_id: str | None = None

        while attempts < max_attempts:
            attempts += 1

            # Campaign 6 (Lot 1, closes a8 P0 section 8): the FULL
            # business authorization runs BEFORE the syscall is issued.
            # Every retry attempt is re-authorized, so every intent
            # binds its own fresh verdict; a stale snapshot from an
            # earlier attempt is not reachable by construction.
            authorization = self.tool_manager.authorize(effective_result, ctx)

            syscall_result = self.syscall_handler.handle(
                Syscall(
                    name="tool.execute",
                    args={
                        "result": effective_result,
                        "ctx": ctx,
                        "process_id": process.process_id.value,
                        "authorization": authorization,
                        "retry_attempt": attempts - 1,
                        "retry_chain_id": retry_chain_id,
                        "retry_parent_syscall_id": parent_syscall_id,
                    },
                )
            )

            execution_state = self._ensure_execution_state(ctx)

            last_entry = execution_state.metadata.get("last_syscall_result")

            if isinstance(last_entry, dict):
                current_syscall_id = last_entry.get("syscall_id")

                if isinstance(current_syscall_id, str):
                    retry_chain_id = retry_chain_id or current_syscall_id
                    parent_syscall_id = current_syscall_id

            # -----------------------------------------------------
            # Retry evaluation (runtime-owned)
            # -----------------------------------------------------
            retry_policy.evaluate(ctx)

            retry_requested = (
                runtime_policy.retry_requested if runtime_policy is not None else False
            )

            # -----------------------------------------------------
            # Success / no retry requested
            # -----------------------------------------------------
            if syscall_result.success or not retry_requested:
                if not syscall_result.success:
                    ctx.extra.setdefault(
                        "errors",
                        [],
                    ).append("tool_execution_failure")

                break

            # -----------------------------------------------------
            # Reset retry edge trigger
            # -----------------------------------------------------
            #
            # Retry request is consumed by runtime loop.
            # Next retry decision must be re-evaluated explicitly.
            # -----------------------------------------------------
            if runtime_policy is not None:
                runtime_policy.retry_requested = False

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
            raise ProcessExecutionAborted(
                f"Process aborted: {error}",
                details={
                    "process_id": proc.process_id.value,
                },
            )

        if proc.status in (
            CognitiveProcessStatus.COMPLETED,
            CognitiveProcessStatus.WAITING_CONFIRMATION,
            CognitiveProcessStatus.BLOCKED,
        ):
            if proc.last_result is None:
                raise RuntimeExecutionContractViolation(
                    f"Process exited in state {proc.status.value} without result"
                )
            return proc.last_result

        if getattr(decision, "result", None) is not None:
            return decision.result

        raise RuntimeExecutionContractViolation(
            "Execution exited without resolvable result"
        )
