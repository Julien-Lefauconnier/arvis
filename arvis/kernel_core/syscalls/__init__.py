# arvis/kernel_core/syscalls/__init__.py

from __future__ import annotations

from arvis.kernel_core.syscalls.syscalls import (
    interrupt_syscalls as _interrupt_syscalls,
)
from arvis.kernel_core.syscalls.syscalls import (
    memory_syscalls as _memory_syscalls,
)
from arvis.kernel_core.syscalls.syscalls import (
    process_syscalls as _process_syscalls,
)
from arvis.kernel_core.syscalls.syscalls import (
    tool_syscalls as _tool_syscalls,
)
from arvis.kernel_core.syscalls.syscalls import (
    vfs_syscalls as _vfs_syscalls,
)

from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import get_syscall, register_syscall

__all__ = [
    "Syscall",
    "SyscallResult",
    "SyscallHandler",
    "register_syscall",
    "get_syscall",
    "_interrupt_syscalls",
    "_memory_syscalls",
    "_process_syscalls",
    "_tool_syscalls",
    "_vfs_syscalls",
]
