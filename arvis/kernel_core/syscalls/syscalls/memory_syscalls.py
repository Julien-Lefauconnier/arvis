# arvis/kernel_core/syscalls/syscalls/memory_syscalls.py

from __future__ import annotations

from typing import Protocol, Any

from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall

class SyscallHandlerLike(Protocol):
    """Minimal handler contract for memory syscalls."""

@register_syscall("memory.read")
def memory_read(
    handler: SyscallHandlerLike,
    key: str,
) -> SyscallResult:
    # V1 placeholder
    return SyscallResult(success=True, result=None)


@register_syscall("memory.write")
def memory_write(
    handler: SyscallHandlerLike,
    key: str,
    value: Any,
) -> SyscallResult:
    # V1 placeholder
    return SyscallResult(success=True)