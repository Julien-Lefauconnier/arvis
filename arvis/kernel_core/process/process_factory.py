# arvis/kernel_core/process/process_factory.py

from __future__ import annotations

from typing import Any, Optional

from arvis.kernel_core.process.process import CognitiveProcess
from arvis.kernel_core.process.process_descriptor import ProcessDescriptor
from arvis.kernel_core.process.process_runtime_state import ProcessRuntimeState
from arvis.kernel_core.process.process_execution_state import ProcessExecutionState
from arvis.kernel_core.process.process_interrupt_state import ProcessInterruptState
from arvis.kernel_core.process.types import (
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)
from arvis.kernel_core.process.priority import CognitivePriority
from arvis.kernel_core.process.budget import CognitiveBudget


class ProcessFactory:
    """
    Single source of truth for process construction.
    """

    @staticmethod
    def create(
        *,
        process_id: CognitiveProcessId,
        kind: CognitiveProcessKind,
        status: CognitiveProcessStatus,
        priority: CognitivePriority,
        budget: CognitiveBudget,
        created_tick: int,
        user_id: Optional[str] = None,
        parent_process_id: Optional[CognitiveProcessId] = None,
        metadata: Optional[dict[str, Any]] = None,
        local_state: Any = None,
    ) -> CognitiveProcess:
        descriptor = ProcessDescriptor(
            process_id=process_id,
            kind=kind,
            priority=priority,
            budget=budget,
            created_tick=created_tick,
            user_id=user_id,
            parent_process_id=parent_process_id,
            metadata=metadata or {},
        )

        runtime = ProcessRuntimeState(
            status=status,
        )

        execution = ProcessExecutionState()
        interrupts = ProcessInterruptState()

        return CognitiveProcess(
            descriptor=descriptor,
            runtime=runtime,
            execution=execution,
            interrupts=interrupts,
            local_state=local_state,
        )
