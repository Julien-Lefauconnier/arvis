# arvis/kernel/pipeline/runtime_bindings.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult


class SyscallHandlerLike(Protocol):
    def handle(self, syscall: Syscall) -> SyscallResult: ...


@dataclass(frozen=True, slots=True)
class PipelineRuntimeBindings:
    syscall_handler: SyscallHandlerLike
    process_id: str
