# arvis/kernel_core/syscalls/__init__.py

from __future__ import annotations

from arvis.kernel_core.syscalls.syscalls import tool_syscalls as _tool_syscalls
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import register_syscall, get_syscall

"""
Kernel syscall package bootstrap.

Importing this package must register all built-in syscalls so that
runtime code can rely on the central registry without having to import
individual syscall modules manually.
"""

__all__ = [
    "Syscall",
    "SyscallResult",
    "SyscallHandler",
    "register_syscall",
    "get_syscall",
    "_tool_syscalls",
]