# arvis/kernel/pipeline/runtime_bindings.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler


@dataclass(frozen=True, slots=True)
class PipelineRuntimeBindings:
    syscall_handler: SyscallHandler
    process_id: str
    run_id: str | None = None
