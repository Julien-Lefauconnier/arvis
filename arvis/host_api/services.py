# arvis/host_api/services.py

"""Mounting host services into the kernel.

The syscall protocol and the service registry through which a host
mounts its own governed services (storage, mail, domain tools).

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.kernel_core.syscalls import (
    Syscall,
    SyscallHandler,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry

__all__ = [
    "KernelServiceRegistry",
    "Syscall",
    "SyscallHandler",
]
